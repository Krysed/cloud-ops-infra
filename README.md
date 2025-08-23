## DevOps infrastructure project.

Purpose of this project is not to build amazing web aplication, but rather to get more hands on approach on infrastructure and automation.

The web template that is used for this project was found on [tooplate.com](https://www.tooplate.com). 
Link to the resource zip can be found here: [link](https://www.tooplate.com/zip-templates/2136_kool_form_pack.zip)
The project was developed on **Ubuntu 24.04**, the provided script `setup.sh` works with said environment. If you plan to run this locally keep in mind that because it is using heavy applications, once the cluster is running it is resource heavy.

### Requirements
- Ubuntu 24.04
- python
- docker
- kubectl
- minikube

## Environment Configuration

There is a setup script `setup.sh` that will install every single tool needed to interact with the project environment. 
Run it to install the required tools, you only need to run the script once.

```bash
./setup.sh
```

This project uses environment variables for configuration. Copy `.env.example` to `.env` and set your values:

```bash
cp .env.example .env
```

Required environment variables:
- `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`
- `REDIS_HOST`, `REDIS_PASSWORD`, `REDIS_PORT`, `REDIS_DB`
- `ENV` (set to `dev` for development)

## Kubernetes Local Setup

This project includes a Kubernetes deployment for local development using Minikube.
Some of the Kubernetes files are ignored and are missing on purpose:
- backend-secret.yaml
- grafana-secret.yaml
- postgres-secret.yaml
- redis-secret.yaml

But there are **.example** files in the directories from the services that you can copy or rename and fill the required fields with the required secrets.
NOTE: each value have to be set with the hashed value using the **base64** hashing algorithm.

For each of the values run following (The values SHOULD match the ones in the .env file):
```bash
echo -n 'value' | base64
```
And copy the output into the respective fields.

### Quick Start

Once the required tools are installed and environment is configured properly you can run the following commands:  

1. **Start Minikube**: `minikube start`
2. **Deploy**: `./kube_check.sh deploy`
3. **Get URL**: `minikube service nginx-service --url -n dev`
4. **Access** the application in your browser

### Cleanup

Once you are finished with the application run following commands to stop all related processes.

```bash
./kube_check.sh cleanup
minikube stop
```

### Quick Commands For running application.

- `./kube_check.sh deploy` - Deploy all resources
- `./kube_check.sh status` - Show deployment status  
- `./kube_check.sh cleanup` - Remove all resources
- `./kube_check.sh help` - Show help

### Architecture

This project implements a complete DevOps infrastructure with observability stack running on Kubernetes.

#### Core Services
- **Frontend**: Nginx serving static HTML/CSS/JS with Bootstrap UI
- **Backend**: FastAPI REST API with OpenTelemetry for gathering data
- **Database**: PostgreSQL with persistent storage for application data
- **Cache**: Redis for sessions and caching with persistent storage
- **Proxy**: Nginx reverse proxy for load balancing and external access

#### Monitoring Stack
- **Grafana**: Visualization dashboards and alerting (accessible via minikube service)
- **Prometheus**: Metrics collection from all services
- **Loki**: Centralized log aggregation
- **Tempo**: Distributed tracing for request flow analysis
- **Mimir**: Metrics storage for historical analysis

#### Infrastructure
- **Namespace**: All services isolated in `dev` namespace
- **Storage**: Persistent volumes for databases and monitoring data
- **Configuration**: Kubernetes ConfigMaps and Secrets for service configuration
- **CI/CD**: GitHub Actions with security scanning, linting, and automated testing

#### Access Points
- **Application**: `minikube service nginx-service --url -n dev`
- **Grafana**: `minikube service grafana-service --url -n dev`
- **API Endpoints**: Available through nginx proxy at `/api/`
