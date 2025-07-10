#!/usr/bin/env bash

set -euo pipefail

wget https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64 -O minikube
chmod 755 minikube 
sudo mv minikube /usr/local/bin/
minikube version
