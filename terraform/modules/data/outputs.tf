output "db_connection_name" {
  description = "Cloud SQL connection name (used by Cloud SQL Proxy)"
  value       = google_sql_database_instance.postgres.connection_name
}

output "db_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "db_name" {
  description = "Database name"
  value       = google_sql_database.app_db.name
}

output "db_user" {
  description = "Database user"
  value       = google_sql_user.app_user.name
}

output "redis_host" {
  description = "Memorystore Redis host IP"
  value       = google_redis_instance.redis.host
}

output "redis_port" {
  description = "Memorystore Redis port"
  value       = google_redis_instance.redis.port
}
