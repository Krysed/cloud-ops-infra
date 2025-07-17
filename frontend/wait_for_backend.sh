#!/usr/bin/env sh

set -eu

HOST=backend
PORT=8000

echo "Waiting for $HOST:$PORT to be ready..."
while ! nc -z $HOST $PORT; do
  sleep 1
done

echo "$HOST:$PORT is up. Starting Nginx..."
exec nginx -g "daemon off;"
