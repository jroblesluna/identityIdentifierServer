#!/bin/bash
set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO_NAME="my-repo"
SERVICE_NAME="identity-server"
SECRET_NAME="firebase-key"

echo "Eliminando servicio de Cloud Run..."
gcloud run services delete "$SERVICE_NAME" --platform=managed --region="$REGION" --quiet || true

echo "Eliminando repositorio de Artifact Registry..."
gcloud artifacts repositories delete "$REPO_NAME" --location="$REGION" --quiet || true

echo "Eliminando secreto..."
gcloud secrets delete "$SECRET_NAME" --quiet || true

echo "Limpieza completa en el proyecto: $PROJECT_ID"