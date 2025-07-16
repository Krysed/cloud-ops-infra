#!/usr/bin/env bash

set -euo pipefail


# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="${PROJECT_ROOT}/k8s"

echo -e "${BLUE}Deploying Kubernetes resources...${NC}"

# Function to wait for resource to be ready
wait_for_resource() {
    local resource_type=$1
    local resource_name=$2
    local namespace=${3:-dev}
    
    echo -e "${YELLOW}Waiting for ${resource_type}/${resource_name} to be ready...${NC}"
    kubectl wait --for=condition=ready ${resource_type}/${resource_name} -n ${namespace} --timeout=300s
}

# Function to check if minikube is running
check_minikube() {
    if ! minikube status > /dev/null 2>&1; then
        echo -e "${RED}Minikube is not running. Please start it first:${NC}"
        echo "minikube start --memory=4096 --cpus=2"
        exit 1
    fi
    echo -e "${GREEN}Minikube is running${NC}"
}

# Function to build images in minikube
build_images() {
    echo -e "${BLUE}Building Docker images in minikube...${NC}"
    
    # Set docker env to minikube
    eval $(minikube docker-env)
    
    # Build all images
    echo -e "${YELLOW}Building backend image...${NC}"
    docker build -t infra-backend:latest "${PROJECT_ROOT}/backend"
    
    echo -e "${YELLOW}Building frontend image...${NC}"
    docker build -t infra-frontend:latest "${PROJECT_ROOT}/frontend"
    
    echo -e "${YELLOW}Building nginx image...${NC}"
    docker build -t infra-nginx:latest "${PROJECT_ROOT}/nginx"
    
    echo -e "${YELLOW}Building postgres image...${NC}"
    docker build -t infra-postgres:latest "${PROJECT_ROOT}/postgres"
    
    echo -e "${YELLOW}Building redis image...${NC}"
    docker build -t infra-redis:latest "${PROJECT_ROOT}/redis"
    
    echo -e "${GREEN}All images built successfully${NC}"
}

# Main deployment function
deploy_resources() {
    echo -e "${BLUE}Deploying Kubernetes resources in order...${NC}"
    
    # 1. Create namespace first
    echo -e "${YELLOW}1. Creating namespace...${NC}"
    kubectl apply -f "${K8S_DIR}/namespace.yaml"
    
    # 2. Storage (PVs are cluster-wide, PVCs are namespaced)
    echo -e "${YELLOW}2. Creating persistent volumes...${NC}"
    kubectl apply -f "${K8S_DIR}/postgres/postgres-pv.yaml"
    kubectl apply -f "${K8S_DIR}/redis/redis-pv.yaml"
    
    # 3. Secrets and configs
    echo -e "${YELLOW}3. Creating secrets and configmaps...${NC}"
    kubectl apply -f "${K8S_DIR}/backend/backend-secret.yaml"
    kubectl apply -f "${K8S_DIR}/backend/backend-configmap.yaml"
    kubectl apply -f "${K8S_DIR}/postgres/postgres-secret.yaml"
    kubectl apply -f "${K8S_DIR}/postgres/postgres-configmap.yaml"
    kubectl apply -f "${K8S_DIR}/redis/redis-secret.yaml"
    kubectl apply -f "${K8S_DIR}/nginx/nginx-configmap.yaml"
    
    # 4. Services (before deployments for DNS)
    echo -e "${YELLOW}4. Creating services...${NC}"
    kubectl apply -f "${K8S_DIR}/postgres/postgres-service.yaml"
    kubectl apply -f "${K8S_DIR}/redis/redis-service.yaml"
    kubectl apply -f "${K8S_DIR}/backend/backend-service.yaml"
    kubectl apply -f "${K8S_DIR}/frontend/frontend-service.yaml"
    
    # 5. Workloads (StatefulSets first, then Deployments)
    echo -e "${YELLOW}5. Creating workloads...${NC}"
    
    # StatefulSets first
    echo -e "${YELLOW}   - PostgreSQL StatefulSet...${NC}"
    kubectl apply -f "${K8S_DIR}/postgres/postgres-statefulset.yaml"
    wait_for_resource "statefulset" "postgres-statefulset"
    
    # Deployments
    echo -e "${YELLOW}   - Redis Deployment...${NC}"
    kubectl apply -f "${K8S_DIR}/redis/redis-deployment.yaml"
    wait_for_resource "deployment" "redis-deployment"
    
    echo -e "${YELLOW}   - Backend Deployment...${NC}"
    kubectl apply -f "${K8S_DIR}/backend/backend-deployment.yaml"
    wait_for_resource "deployment" "backend-deployment"
    
    echo -e "${YELLOW}   - Frontend Deployment...${NC}"
    kubectl apply -f "${K8S_DIR}/frontend/frontend-deployment.yaml"
    wait_for_resource "deployment" "frontend-deployment"
    
    echo -e "${YELLOW}   - Nginx Deployment...${NC}"
    kubectl apply -f "${K8S_DIR}/nginx/nginx-deployment.yaml"
    wait_for_resource "deployment" "nginx-deployment"
    
    # 6. External access
    echo -e "${YELLOW}6. Creating external access...${NC}"
    kubectl apply -f "${K8S_DIR}/nginx/nginx-service.yaml"
    
    echo -e "${GREEN}✅ All resources deployed successfully!${NC}"
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Deployment Status:${NC}"
    echo ""
    
    echo -e "${YELLOW}Pods:${NC}"
    kubectl get pods -n dev -o wide
    echo ""
    
    echo -e "${YELLOW}Services:${NC}"
    kubectl get svc -n dev
    echo ""
    
    echo -e "${YELLOW}PersistentVolumes:${NC}"
    kubectl get pv
    echo ""
    
    echo -e "${YELLOW}PersistentVolumeClaims:${NC}"
    kubectl get pvc -n dev
    echo ""
    
    # Get external access URL
    echo -e "${YELLOW}External Access:${NC}"
    NGINX_URL=$(minikube service nginx-service --url -n dev)
    echo -e "${GREEN}Application available at: ${NGINX_URL}${NC}"
    echo ""
    
    echo -e "${BLUE}Deployment completed successfully!${NC}"
    echo -e "${GREEN}Your application is ready to use.${NC}"
}

# Function to clean up resources
cleanup() {
    echo -e "${RED}Cleaning up all resources...${NC}"
    kubectl delete namespace dev --ignore-not-found=true
    kubectl delete pv postgres-pv redis-pv --ignore-not-found=true
    echo -e "${GREEN}Cleanup completed${NC}"
}

# Main script logic
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
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
