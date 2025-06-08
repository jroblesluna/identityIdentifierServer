#!/bin/bash

set -e

# Variables del proyecto
PROJECT_ID="identityverifierapp"
REGION="us-central1"
SERVICE_NAME="identity-server"
REPO_NAME="my-repo"
IMAGE_NAME="identity-server"
TAG="latest"
SECRET_NAME="FIREBASE_KEY"
FIREBASE_KEY_PATH="./firebase_key.json"
STORAGE_BUCKET_NAME="identityverifierapp.firebasestorage.com"
CLOUD_RUN_SA="cloud-run-sa"
CLOUD_RUN_SA_EMAIL="$CLOUD_RUN_SA@$PROJECT_ID.iam.gserviceaccount.com"

# Validar existencia de archivo de clave
if [ ! -f "$FIREBASE_KEY_PATH" ]; then
  echo "❌ Error: No se encontró el archivo $FIREBASE_KEY_PATH"
  exit 1
fi

echo "⏳ Autenticando y configurando proyecto..."
gcloud config set project "$PROJECT_ID"

# Verificar si el repositorio Artifact Registry existe
echo "🔍 Verificando si el repositorio '$REPO_NAME' existe..."
if gcloud artifacts repositories list --location="$REGION" --format="value(name)" 2>/dev/null | grep -q "^$REPO_NAME$"; then
  echo "✅ Repositorio Artifact Registry '$REPO_NAME' ya existe."
else
  echo "📦 Repositorio Artifact Registry '$REPO_NAME' no encontrado. Creando..."
  gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Docker repo for $SERVICE_NAME"
fi

# Subir imagen a Artifact Registry
echo "🔧 Construyendo imagen Docker..."
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:$TAG"

# Crear cuenta de servicio si no existe
if ! gcloud iam service-accounts describe "$CLOUD_RUN_SA_EMAIL" > /dev/null 2>&1; then
  echo "🆕 Creando cuenta de servicio $CLOUD_RUN_SA..."
  gcloud iam service-accounts create "$CLOUD_RUN_SA" \
    --display-name="Cloud Run Service Account"
else
  echo "✅ Cuenta de servicio $CLOUD_RUN_SA ya existe."
fi

# Crear secreto si no existe
if ! gcloud secrets describe "$SECRET_NAME" > /dev/null 2>&1; then
  echo "🔐 Creando secreto $SECRET_NAME..."
  gcloud secrets create "$SECRET_NAME" \
    --replication-policy="automatic" \
    --data-file="$FIREBASE_KEY_PATH"
else
  echo "♻️ Secreto $SECRET_NAME ya existe, actualizando contenido..."
  gcloud secrets versions add "$SECRET_NAME" --data-file="$FIREBASE_KEY_PATH"
fi

# Otorgar acceso al secreto
echo "🔐 Otorgando acceso a secretos a $CLOUD_RUN_SA_EMAIL..."
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --member="serviceAccount:$CLOUD_RUN_SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

# Otorgar permiso para ejecutar Cloud Run si fuera necesario (opcional)
echo "🔒 Verificando permisos del service account para Cloud Run..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$CLOUD_RUN_SA_EMAIL" \
  --role="roles/run.invoker" \
  --quiet || true

# Desplegar servicio en Cloud Run
echo "🚀 Desplegando en Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:$TAG" \
  --region="$REGION" \
  --platform=managed \
  --set-env-vars="STORAGE_BUCKET_NAME=$STORAGE_BUCKET_NAME" \
  --set-secrets="/secrets/$SECRET_NAME=${SECRET_NAME}:latest" \
  --allow-unauthenticated \
  --service-account="$CLOUD_RUN_SA_EMAIL"

echo "✅ ¡Despliegue completo!"