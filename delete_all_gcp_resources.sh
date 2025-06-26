#!/bin/bash
set -e

PROJECT_ID="identityverifierapp"
REGION="us-central1"
REPO_NAME="my-repo"
SERVICE_NAME="identity-server"
SECRET_NAME="FIREBASE_KEY"

gcloud config set project $PROJECT_ID

echo "🧹 Iniciando limpieza en el proyecto: $PROJECT_ID"

# Eliminar servicio Cloud Run si existe
if gcloud run services describe "$SERVICE_NAME" --platform=managed --region="$REGION" &> /dev/null; then
  echo "🗑️  Eliminando servicio de Cloud Run..."
  gcloud run services delete "$SERVICE_NAME" --platform=managed --region="$REGION" --quiet
else
  echo "✅ Servicio Cloud Run '$SERVICE_NAME' ya estaba eliminado."
fi

# Eliminar repositorio de Artifact Registry si existe
if gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &> /dev/null; then
  echo "🗑️  Eliminando repositorio Artifact Registry..."
  gcloud artifacts repositories delete "$REPO_NAME" --location="$REGION" --quiet
else
  echo "✅ Repositorio '$REPO_NAME' ya estaba eliminado."
fi

# Eliminar secreto si existe
if gcloud secrets describe "$SECRET_NAME" &> /dev/null; then
  echo "🗑️  Eliminando secreto '$SECRET_NAME'..."
  gcloud secrets delete "$SECRET_NAME" --quiet
else
  echo "✅ Secreto '$SECRET_NAME' ya estaba eliminado."
fi

# Eliminar job de Cloud Scheduler si existe
echo "🗓️  Verificando existencia del job 'cronVerifyId'..."
if gcloud scheduler jobs describe cronVerifyId --location=$REGION &> /dev/null; then
  echo "🗑️  Eliminando job de Cloud Scheduler 'cronVerifyId'..."
  gcloud scheduler jobs delete cronVerifyId --location=$REGION --quiet
else
  echo "✅ Job 'cronVerifyId' ya estaba eliminado."
fi

# (Opcional: desactivar la API solo si no planeas volver a usar Scheduler pronto)
echo "🛑 Desactivando API de Cloud Scheduler..."
gcloud services disable cloudscheduler.googleapis.com --project=$PROJECT_ID

echo -e "\n🎉 Limpieza completa sin errores."