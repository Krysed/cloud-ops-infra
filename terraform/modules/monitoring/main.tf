# Dedicated namespace for the full observability stack
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = var.namespace
    labels = {
      name       = var.namespace
      managed-by = "terraform"
    }
  }
}

# ============================================================
# kube-prometheus-stack
# Includes: Prometheus, Grafana, AlertManager, node-exporter,
#           kube-state-metrics
# ============================================================
resource "helm_release" "kube_prometheus_stack" {
  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "65.1.1"

  # Increase timeout - CRDs take time on first install
  timeout = 600

  values = [
    yamlencode({
      grafana = {
        adminPassword = var.grafana_admin_password
        persistence = {
          enabled          = true
          size             = var.storage_size_grafana
          storageClassName = "standard"
        }
        # Expose via LoadBalancer so CI can get the URL
        service = {
          type = "LoadBalancer"
        }
        sidecar = {
          dashboards = {
            enabled         = true
            label           = "grafana_dashboard"
            labelValue      = "1"
            searchNamespace = "ALL"
          }
        }
        # Pre-provision all datasources automatically
        additionalDataSources = [
          {
            name   = "Loki"
            type   = "loki"
            url    = "http://loki.${var.namespace}.svc.cluster.local:3100"
            access = "proxy"
          },
          {
            name   = "Tempo"
            type   = "tempo"
            url    = "http://tempo.${var.namespace}.svc.cluster.local:3200"
            access = "proxy"
          },
          {
            name   = "Mimir"
            type   = "prometheus"
            url    = "http://mimir.${var.namespace}.svc.cluster.local:9009/prometheus"
            access = "proxy"
          }
        ]
      }

      prometheus = {
        prometheusSpec = {
          retention = "${var.prometheus_retention_days}d"

          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = "standard"
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = var.storage_size_prometheus
                  }
                }
              }
            }
          }

          # Remote write to Mimir for long-term storage
          remoteWrite = [
            {
              url = "http://mimir.${var.namespace}.svc.cluster.local:9009/api/v1/push"
            }
          ]
        }
      }

      alertmanager = {
        enabled = true
      }
    })
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# ============================================================
# Loki (single binary mode - suitable for dev)
# ============================================================
resource "helm_release" "loki" {
  name       = "loki"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "6.20.0"

  values = [
    yamlencode({
      deploymentMode = "SingleBinary"

      loki = {
        commonConfig = {
          replication_factor = 1
        }
        storage = {
          type = "filesystem"
        }
        limits_config = {
          retention_period = "${var.loki_retention_days}d"
        }
        auth_enabled = false
      }

      singleBinary = {
        replicas = 1
        persistence = {
          enabled          = true
          size             = var.storage_size_loki
          storageClass     = "standard"
        }
      }

      # Disable unused components in single-binary mode
      backend = { replicas = 0 }
      read    = { replicas = 0 }
      write   = { replicas = 0 }
      minio   = { enabled = false }
    })
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# ============================================================
# Promtail (DaemonSet - ships logs from all nodes to Loki)
# ============================================================
resource "helm_release" "promtail" {
  name       = "promtail"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "promtail"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "6.16.6"

  values = [
    yamlencode({
      config = {
        clients = [
          {
            url = "http://loki.${var.namespace}.svc.cluster.local:3100/loki/api/v1/push"
          }
        ]
      }
    })
  ]

  depends_on = [helm_release.loki]
}

# ============================================================
# Tempo (distributed tracing backend)
# ============================================================
resource "helm_release" "tempo" {
  name       = "tempo"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "tempo"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "1.10.3"

  values = [
    yamlencode({
      persistence = {
        enabled          = true
        size             = var.storage_size_tempo
        storageClassName = "standard"
      }
      tempo = {
        storage = {
          trace = {
            backend = "local"
            local = {
              path = "/var/tempo/traces"
            }
          }
        }
        # OTLP receiver endpoints
        receivers = {
          otlp = {
            protocols = {
              grpc = { endpoint = "0.0.0.0:4317" }
              http = { endpoint = "0.0.0.0:4318" }
            }
          }
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# ============================================================
# Mimir (long-term metrics storage)
# Deployed as a single-binary Deployment (not the distributed chart)
# to keep resource usage minimal in the dev environment
# ============================================================
resource "kubernetes_persistent_volume_claim" "mimir" {
  metadata {
    name      = "mimir-pvc"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
  }
  spec {
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = "standard"
    resources {
      requests = {
        storage = var.storage_size_mimir
      }
    }
  }
}

resource "kubernetes_deployment" "mimir" {
  metadata {
    name      = "mimir"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "mimir"
    }
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "mimir"
      }
    }
    template {
      metadata {
        labels = {
          app = "mimir"
        }
      }
      spec {
        container {
          name  = "mimir"
          image = "grafana/mimir:2.13.0"
          args  = ["-config.file=/etc/mimir/mimir.yaml"]

          port {
            container_port = 9009
            name           = "http"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "256Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }

          volume_mount {
            name       = "mimir-storage"
            mount_path = "/data"
          }

          volume_mount {
            name       = "mimir-config"
            mount_path = "/etc/mimir"
          }
        }

        volume {
          name = "mimir-storage"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.mimir.metadata[0].name
          }
        }

        volume {
          name = "mimir-config"
          config_map {
            name = kubernetes_config_map.mimir_config.metadata[0].name
          }
        }
      }
    }
  }

  depends_on = [kubernetes_namespace.monitoring]
}

resource "kubernetes_config_map" "mimir_config" {
  metadata {
    name      = "mimir-config"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
  }

  data = {
    "mimir.yaml" = <<-EOT
      target: all
      multitenancy_enabled: false

      common:
        storage:
          backend: filesystem
          filesystem:
            dir: /data/mimir

      blocks_storage:
        filesystem:
          dir: /data/mimir/blocks

      ruler_storage:
        filesystem:
          dir: /data/mimir/ruler

      alertmanager_storage:
        filesystem:
          dir: /data/mimir/alertmanager

      server:
        http_listen_port: 9009
        grpc_listen_port: 9095
    EOT
  }
}

# ============================================================
# Grafana dashboard ConfigMaps
# Sidecar watches for ConfigMaps with label grafana_dashboard=1
# and loads them automatically without restarting Grafana.
# Source of truth: grafana/dashboards/ (shared with Minikube provisioning)
# ============================================================
locals {
  dashboards_path = "${path.module}/../../../grafana/dashboards"
}

resource "kubernetes_config_map" "dashboard_backend_health" {
  metadata {
    name      = "dashboard-backend-health"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      grafana_dashboard = "1"
    }
  }

  data = {
    "backend_health.json" = file("${local.dashboards_path}/backend_health.json")
  }

  depends_on = [helm_release.kube_prometheus_stack]
}

resource "kubernetes_service" "mimir" {
  metadata {
    name      = "mimir"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "mimir"
    }
  }

  spec {
    selector = {
      app = "mimir"
    }
    port {
      name        = "http"
      port        = 9009
      target_port = 9009
    }
    type = "ClusterIP"
  }
}
