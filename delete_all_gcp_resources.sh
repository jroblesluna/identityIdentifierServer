#!/bin/bash
set -e

PROJECT_ID="identityverifierapp"
REGION="us-central1"
REPO_NAME="my-repo"
SERVICE_NAME="identity-server"
SECRET_NAME="FIREBASE_KEY"
CLOUD_RUN_SA="cloud-run-sa"
CLOUD_RUN_SA_EMAIL="$CLOUD_RUN_SA@$PROJECT_ID.iam.gserviceaccount.com"
DOMAIN="identity-api.robles.ai"


gcloud config set project $PROJECT_ID

echo "🧹 Iniciando limpieza en el proyecto: $PROJECT_ID"

# Eliminar dominio si existe
if gcloud domains describe "$DOMAIN" &> /dev/null; then
  echo "🗑️  Eliminando dominio '$DOMAIN'..."
  gcloud domains delete "$DOMAIN" --quiet
else
  echo "✅ Dominio '$DOMAIN' ya estaba eliminado."
fi


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

# Eliminar cuenta de servicio si existe
if gcloud iam service-accounts describe "$CLOUD_RUN_SA_EMAIL" &> /dev/null; then
  echo "🗑️  Eliminando cuenta de servicio '$CLOUD_RUN_SA_EMAIL'..."
  gcloud iam service-accounts delete "$CLOUD_RUN_SA_EMAIL" --quiet
else
  echo "✅ Cuenta de servicio '$CLOUD_RUN_SA_EMAIL' ya estaba eliminada."
fi

# Asegurando que el scheduler esté activo si no lo está
if ! gcloud services list --enabled --project=$PROJECT_ID | grep -q "cloudscheduler.googleapis.com"; then
  echo "🔄 Activando API de Cloud Scheduler..."
  gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID
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