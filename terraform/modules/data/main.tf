# Private service connection - required for Cloud SQL private IP
resource "google_compute_global_address" "private_ip_range" {
  name          = "private-ip-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = var.network_id
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = var.network_id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

# ============================================================
# Cloud SQL - PostgreSQL (replaces postgres StatefulSet)
# ============================================================
resource "google_sql_database_instance" "postgres" {
  name             = var.db_instance_name
  database_version = var.db_version
  region           = var.region
  project          = var.project_id

  depends_on = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier    = var.db_tier
    edition = "ENTERPRISE"

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.network_id
    }

    backup_configuration {
      enabled    = var.backup_enabled
      start_time = var.backup_start_time

      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    maintenance_window {
      day  = 7 # Sunday
      hour = 3
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    # Query Insights for performance monitoring
    insights_config {
      query_insights_enabled = true
    }
  }

  # IMPORTANT!: set to true before production use
  deletion_protection = false
}

resource "google_sql_database" "app_db" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
}

resource "google_sql_user" "app_user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
  project  = var.project_id
}

# ============================================================
# Memorystore - Redis (replaces local Redis Deployment)
# ============================================================
resource "google_redis_instance" "redis" {
  name               = var.redis_instance_name
  tier               = var.redis_tier
  memory_size_gb     = var.redis_memory_size_gb
  region             = var.region
  project            = var.project_id
  redis_version      = var.redis_version
  authorized_network = var.network_id

  labels = {
    managed-by = "terraform"
  }
}
