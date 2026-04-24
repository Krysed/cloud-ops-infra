# ============================================================
# Dev Environment - Terraform Variables
# ============================================================
# Replace placeholder GCP project info.
#
# Use environment variables instead:
#   export TF_VAR_project_id="your_project_id"
#   export TF_VAR_project_number="your_project_number"
#   export TF_VAR_db_password="your_password"
#   export TF_VAR_app_secret_key="your_secret_key"
#   export TF_VAR_grafana_admin_password="your_grafana_password"
# ============================================================

region      = "us-central1"
environment = "dev"
