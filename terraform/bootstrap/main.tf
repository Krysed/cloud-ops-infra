terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Intentionally local state - this config bootstraps the remote state bucket.
  # Do NOT add a GCS backend here.
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

resource "google_storage_bucket" "terraform_state" {
  name          = "infra-terraform-state-66926-${var.environment}"
  location      = var.region
  force_destroy = true # false will prevent destroying the bucket when it contains any files

  versioning {
    enabled = true
  }

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      num_newer_versions = 10
    }
    action {
      type = "Delete"
    }
  }
}

output "bucket_name" {
  value       = google_storage_bucket.terraform_state.name
  description = "GCS bucket name for Terraform state"
}

# ============================================================
# Artifact Registry for Docker images
# ============================================================
resource "google_artifact_registry_repository" "docker_images" {
  location      = var.region
  repository_id = "infra-project-ms-docker-images"
  format        = "DOCKER"
  description   = "Docker images for the project like backend image"
}

output "docker_registry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker_images.repository_id}"
  description = "Docker registry base URL"
}
