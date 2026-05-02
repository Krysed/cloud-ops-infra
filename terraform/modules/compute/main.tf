# GKE Cluster (regional for HA)
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region
  project  = var.project_id

  # node pool managed separately
  remove_default_node_pool = true
  initial_node_count       = 1

  # VPC-native networking, alias IP ranges
  networking_mode = "VPC_NATIVE"
  network         = var.network_name
  subnetwork      = var.subnet_name

  ip_allocation_policy {
    cluster_secondary_range_name  = var.pods_range_name
    services_secondary_range_name = var.services_range_name
  }

  # Private cluster, nodes have no public IPs
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  # Allow access to control plane from anywhere restrict in prod
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "all"
    }
  }

  # Workload Identity allows pods to authenticate as GCP service accounts
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
    }
  }

  # Use GCP's managed logging/monitoring
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  # Auto-upgrade via REGULAR channel
  release_channel {
    channel = "REGULAR"
  }

  # Daily 4h window at 03:00 UTC satisfies GCP's requirement of
  # >= 48h maintenance availability per 32-day period (4h × 32d = 128h).
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }

  lifecycle {
    ignore_changes = [initial_node_count]
  }
}

# Node Pool with autoscaling
resource "google_container_node_pool" "primary_nodes" {
  name     = "${var.cluster_name}-node-pool"
  location = var.region
  cluster  = google_container_cluster.primary.name
  project  = var.project_id

  initial_node_count = var.initial_node_count

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type = var.node_machine_type
    disk_size_gb = var.node_disk_size_gb
    disk_type    = "pd-standard"

    service_account = var.gke_service_account_email

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    # Required for Workload Identity on the node
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      cluster = var.cluster_name
    }

    tags = ["gke-node", var.cluster_name]

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }

  lifecycle {
    ignore_changes = [initial_node_count]
  }
}
