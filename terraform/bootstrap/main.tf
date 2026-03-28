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
  name          = "infra-terraform-state-${var.environment}"
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
