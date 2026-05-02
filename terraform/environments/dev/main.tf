terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.33"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.16"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }

  backend "gcs" {
    bucket = "infra-terraform-state-66926-dev"
    prefix = "terraform/state"
  }
}

# ============================================================
# Providers
# ============================================================

provider "google" {
  project = var.project_id
  region  = var.region
}

# kubernetes + helm providers are configured AFTER the GKE cluster
# is created, using its endpoint and credentials as data sources.
# This is the standard pattern for managing GKE with Terraform.
data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${module.compute.cluster_endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.compute.cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = "https://${module.compute.cluster_endpoint}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(module.compute.cluster_ca_certificate)
  }
}

# ============================================================
# Enable required GCP APIs
# Must run before any module that creates managed resources.
# disable_on_destroy = false prevents accidental breakage of
# resources that were created while the API was enabled.
# ============================================================
resource "google_project_service" "apis" {
  for_each = toset([
    "compute.googleapis.com",
    "container.googleapis.com",
    "servicenetworking.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "artifactregistry.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# GCP API activation takes 30-60s to propagate after the request succeeds.
# Without this wait, resources that depend on newly enabled APIs fail with 403.
resource "time_sleep" "wait_for_apis" {
  create_duration = "60s"
  depends_on      = [google_project_service.apis]
}

# ============================================================
# Module: Security
# Created first - GKE node SA is needed by the compute module
# ============================================================
module "security" {
  source = "../../modules/security"

  project_id     = var.project_id
  project_number = var.project_number
  gke_namespace  = "dev"

  db_password            = var.db_password
  app_secret_key         = var.app_secret_key
  grafana_admin_password = var.grafana_admin_password

  depends_on = [time_sleep.wait_for_apis]
}

# ============================================================
# Module: Networking
# VPC, subnet (with secondary ranges), Cloud NAT, firewall
# ============================================================
module "networking" {
  source = "../../modules/networking"

  project_id    = var.project_id
  region        = var.region
  network_name  = "infra-vpc-${var.environment}"
  subnet_name   = "infra-subnet-${var.environment}"
  subnet_cidr   = "10.0.0.0/24"
  pods_cidr     = "10.1.0.0/16"
  services_cidr = "10.2.0.0/16"

  depends_on = [time_sleep.wait_for_apis]
}

# ============================================================
# Module: Data
# Cloud SQL (PostgreSQL 17) + Memorystore (Redis 7)
# Uses private IP - requires networking module first
# ============================================================
module "data" {
  source = "../../modules/data"

  project_id = var.project_id
  region     = var.region
  network_id = module.networking.vpc_self_link

  db_instance_name = "infra-postgres-${var.environment}"
  db_tier          = "db-f1-micro" # cheapest tier for dev
  db_name          = "app_db"
  db_user          = "app_user"
  db_password      = var.db_password
  backup_enabled   = false # disable backups in dev to save cost

  redis_instance_name  = "infra-redis-${var.environment}"
  redis_tier           = "BASIC"
  redis_memory_size_gb = 1

  depends_on = [module.networking, time_sleep.wait_for_apis]
}

# ============================================================
# Module: Compute
# Regional GKE cluster with autoscaling node pool
# ============================================================
module "compute" {
  source = "../../modules/compute"

  project_id                = var.project_id
  region                    = var.region
  cluster_name              = "infra-cluster-${var.environment}"
  network_name              = module.networking.vpc_name
  subnet_name               = module.networking.subnet_name
  pods_range_name           = module.networking.pods_range_name
  services_range_name       = module.networking.services_range_name
  gke_service_account_email = module.security.gke_node_sa_email

  # e2-standard-2: 2 vCPU, 8 GB RAM - enough for the full stack in dev
  node_machine_type  = "e2-standard-2"
  initial_node_count = 1
  min_node_count     = 1
  max_node_count     = 3

  depends_on = [module.networking, module.security, time_sleep.wait_for_apis]
}

# ============================================================
# Module: Monitoring
# Full observability stack deployed to GKE:
#   Prometheus + Grafana + AlertManager (kube-prometheus-stack)
#   Loki + Promtail + Tempo + Mimir
# ============================================================
module "monitoring" {
  source = "../../modules/monitoring"

  namespace              = "monitoring"
  grafana_admin_password = var.grafana_admin_password

  # Reduced retention for dev
  prometheus_retention_days = 7
  loki_retention_days       = 14

  storage_size_grafana    = "5Gi"
  storage_size_prometheus = "10Gi"
  storage_size_loki       = "10Gi"
  storage_size_tempo      = "5Gi"
  storage_size_mimir      = "10Gi"

  depends_on = [module.compute]
}

# ============================================================
# Workload Identity binding
# Binds the Kubernetes ServiceAccount "app-sa" (in the app
# namespace) to the GCP ServiceAccount, allowing pods to
# authenticate as app_sa without credentials.
#
# Must live here (not in the security module) because the
# Identity Pool {project_id}.svc.id.goog is created by GKE
# and only exists after module.compute completes.
# ============================================================
resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = module.security.app_sa_id
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[dev/app-sa]"

  depends_on = [module.compute, module.security]
}
