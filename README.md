## DevOps infrastructure project.

Purpose of this project is not to build amazing web aplication, but rather to get more hands on approach on infrastructure and automation.

The web template that is used fot this project was found on [tooplate.com](https://www.tooplate.com). 
Link to the resource zip: [link](https://www.tooplate.com/zip-templates/2136_kool_form_pack.zip)

There is a setup script `setup.sh` that will install every single tool needed to interact with the project environment.

## Environment Configuration

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

### Quick Start

1. **Start Minikube**: `minikube start --memory=4096 --cpus=2`
2. **Deploy**: `./kube_check.sh deploy`
3. **Get URL**: `minikube service nginx-service --url -n dev`
4. **Access** the application in your browser

### Commands

- `./kube_check.sh deploy` - Deploy all resources
- `./kube_check.sh status` - Show deployment status  
- `./kube_check.sh cleanup` - Remove all resources
- `./kube_check.sh help` - Show help

### Architecture

The deployment includes Frontend (Nginx), Backend (FastAPI), Database (PostgreSQL), Cache (Redis), and Reverse Proxy (Nginx) running in a `dev` namespace with persistent storage.

### Cleanup

```bash
./kube_check.sh cleanup
minikube stop
```
