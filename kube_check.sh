#!/usr/bin/env bash

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="${PROJECT_ROOT}/k8s"

# ─── Service lists ────────────────────────────────────────────────────────────
# Edit these arrays to add or remove services.

BUILD_IMAGES=(backend frontend nginx postgres redis grafana loki mimir tempo prometheus)

SERVICES_WITH_PV=(postgres redis grafana loki mimir tempo)
SERVICES_WITH_SECRET=(backend postgres redis grafana)
SERVICES_WITH_CONFIGMAP=(backend postgres grafana loki promtail mimir tempo prometheus)
SERVICES_WITH_K8S_SERVICE=(postgres redis backend frontend grafana loki mimir tempo prometheus)

# Deployments are ordered, Promtail (DaemonSet) is deployed between these two groups.
DEPLOYMENTS_PRE_PROMTAIL=(redis backend frontend nginx grafana loki)
DEPLOYMENTS_POST_PROMTAIL=(mimir tempo prometheus)
# ─────────────────────────────────────────────────────────────────────────────

log_info()  { echo -e "${BLUE}${1}${NC}"; }
log_ok()    { echo -e "${GREEN}${1}${NC}"; }
log_step()  { echo -e "${YELLOW}${1}${NC}"; }
log_error() { echo -e "${RED}${1}${NC}"; }

wait_for_resource() {
    local resource_type=$1
    local resource_name=$2
    local namespace=${3:-dev}

    log_step "Waiting for ${resource_type}/${resource_name} to be ready..."
    if [[ "${resource_type}" == "statefulset" ]]; then
        kubectl wait --for=jsonpath='{.status.readyReplicas}'=1 "${resource_type}/${resource_name}" -n "${namespace}" --timeout=300s
    elif [[ "${resource_type}" == "deployment" ]]; then
        kubectl wait --for=condition=available "${resource_type}/${resource_name}" -n "${namespace}" --timeout=300s
    else
        kubectl wait --for=condition=ready "${resource_type}/${resource_name}" -n "${namespace}" --timeout=300s
    fi
}

check_minikube() {
    if ! minikube status > /dev/null 2>&1; then
        log_error "Minikube is not running. Please start it first:"
        echo "minikube start"
        exit 1
    fi
    log_ok "Minikube is running"
}

build_images() {
    log_info "Building Docker images in minikube..."
    eval "$(minikube docker-env)"

    for name in "${BUILD_IMAGES[@]}"; do
        log_step "Building ${name} image..."
        docker build -t "infra-${name}:latest" "${PROJECT_ROOT}/${name}"
    done

    log_ok "All images built successfully"
}

deploy_resources() {
    log_info "Deploying Kubernetes resources in order..."

    log_step "1. Creating namespace..."
    kubectl apply -f "${K8S_DIR}/namespace.yaml"

    log_step "2. Creating persistent volumes..."
    for svc in "${SERVICES_WITH_PV[@]}"; do
        kubectl apply -f "${K8S_DIR}/${svc}/${svc}-pv.yaml"
    done

    log_step "3. Creating secrets and configmaps..."
    for svc in "${SERVICES_WITH_SECRET[@]}"; do
        kubectl apply -f "${K8S_DIR}/${svc}/${svc}-secret.yaml"
    done
    for svc in "${SERVICES_WITH_CONFIGMAP[@]}"; do
        kubectl apply -f "${K8S_DIR}/${svc}/${svc}-configmap.yaml"
    done

    log_step "4. Creating services..."
    for svc in "${SERVICES_WITH_K8S_SERVICE[@]}"; do
        kubectl apply -f "${K8S_DIR}/${svc}/${svc}-service.yaml"
    done

    log_step "5. Creating workloads..."

    log_step "   - PostgreSQL StatefulSet..."
    kubectl apply -f "${K8S_DIR}/postgres/postgres-statefulset.yaml"
    wait_for_resource "statefulset" "postgres-statefulset"

    for name in "${DEPLOYMENTS_PRE_PROMTAIL[@]}"; do
        log_step "   - ${name^} Deployment..."
        kubectl apply -f "${K8S_DIR}/${name}/${name}-deployment.yaml"
        wait_for_resource "deployment" "${name}-deployment"
    done

    log_step "   - Promtail DaemonSet..."
    kubectl apply -f "${K8S_DIR}/promtail/promtail-daemonset.yaml"
    kubectl rollout status daemonset/promtail -n dev --timeout=300s

    for name in "${DEPLOYMENTS_POST_PROMTAIL[@]}"; do
        log_step "   - ${name^} Deployment..."
        kubectl apply -f "${K8S_DIR}/${name}/${name}-deployment.yaml"
        wait_for_resource "deployment" "${name}-deployment"
    done

    log_step "6. Creating external access..."
    kubectl apply -f "${K8S_DIR}/nginx/nginx-service.yaml"

    log_ok "All resources deployed successfully!"
}

show_status() {
    log_info "Deployment Status:"
    echo ""

    log_step "Pods:"
    kubectl get pods -n dev -o wide
    echo ""

    log_step "Services:"
    kubectl get svc -n dev
    echo ""

    log_step "PersistentVolumes:"
    kubectl get pv
    echo ""

    log_step "PersistentVolumeClaims:"
    kubectl get pvc -n dev
    echo ""

    log_step "External Access:"
    NGINX_URL=$(minikube service nginx-service --url -n dev)
    log_ok "Application available at: ${NGINX_URL}"
    echo ""

    log_info "Deployment completed successfully!"
    log_ok "Your application is ready to use."
}

cleanup() {
    log_error "Cleaning up all resources..."
    kubectl delete namespace dev --ignore-not-found=true
    kubectl delete pv "${SERVICES_WITH_PV[@]/%/-pv}" --ignore-not-found=true
    kubectl delete clusterrole promtail --ignore-not-found=true
    kubectl delete clusterrolebinding promtail --ignore-not-found=true
    log_ok "Cleanup completed"
}

case "${1:-deploy}" in
    "deploy")
        check_minikube
        build_images
        deploy_resources
        show_status
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "help")
        echo "Usage: $0 [deploy|status|cleanup|help]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Build images and deploy all resources (default)"
        echo "  status   - Show current deployment status"
        echo "  cleanup  - Remove all resources"
        echo "  help     - Show this help message"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
