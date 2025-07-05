#!/bin/bash
set -e

# ──────── VARIABLES DEL PROYECTO ────────
PROJECT_ID="identityverifierapp"
REGION="us-central1"
SERVICE_NAME="identity-server"
REPO_NAME="my-repo"
IMAGE_NAME="identity-server"
TAG="latest"
SECRET_NAME="FIREBASE_KEY"
FIREBASE_KEY_PATH="./firebase_key.json"
STORAGE_BUCKET_NAME="identityverifierapp.firebasestorage.app"
CLOUD_RUN_SA="cloud-run-sa"
CLOUD_RUN_SA_EMAIL="$CLOUD_RUN_SA@$PROJECT_ID.iam.gserviceaccount.com"
DOMAIN="identity-api.robles.ai"


gcloud config set project $PROJECT_ID

echo "📁 Proyecto: $PROJECT_ID"
echo "🧭 Región: $REGION"
echo "🔐 Secreto: $SECRET_NAME"
echo "📦 Repositorio: $REPO_NAME"
echo "⚙️  Imagen: $IMAGE_NAME:$TAG"
echo "👤 Cuenta de servicio: $CLOUD_RUN_SA_EMAIL"
echo "───────────────────────────────────────────────"

# ──────── VALIDAR ARCHIVO DE CLAVE ────────
if [ ! -f "$FIREBASE_KEY_PATH" ]; then
  echo "🛑 ERROR: No se encontró el archivo $FIREBASE_KEY_PATH"
  exit 1
fi

# ──────── CONFIGURAR PROYECTO ────────
echo "🛠️ Configurando proyecto en gcloud..."
gcloud config set project "$PROJECT_ID"

# ──────── REPOSITORIO ARTIFACT REGISTRY ────────
echo "🔍 Verificando repositorio '$REPO_NAME'..."
if gcloud artifacts repositories list --location="$REGION" --format="value(name)" 2>/dev/null | grep -q "^$REPO_NAME$"; then
  echo "🟢 Repositorio '$REPO_NAME' ya existe."
else
  echo "📦 [CREANDO] Repositorio '$REPO_NAME'..."
  gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Docker repo for $SERVICE_NAME"
fi

# ──────── CONSTRUIR IMAGEN DOCKER ────────
echo "🔧 Construyendo imagen Docker y subiendo a Artifact Registry..."
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:$TAG"

# ──────── CUENTA DE SERVICIO ────────
echo "👤 Verificando cuenta de servicio '$CLOUD_RUN_SA_EMAIL'..."
if ! gcloud iam service-accounts describe "$CLOUD_RUN_SA_EMAIL" > /dev/null 2>&1; then
  echo "🆕 [CREANDO] Cuenta de servicio '$CLOUD_RUN_SA'..."
  gcloud iam service-accounts create "$CLOUD_RUN_SA" --display-name="Cloud Run Service Account"
else
  echo "🟢 Cuenta de servicio '$CLOUD_RUN_SA' ya existe."
fi

# ──────── SECRETO FIREBASE ────────
echo "🔐 Verificando secreto '$SECRET_NAME'..."
if ! gcloud secrets describe "$SECRET_NAME" > /dev/null 2>&1; then
  echo "🔐 [CREANDO] Secreto '$SECRET_NAME'..."
  gcloud secrets create "$SECRET_NAME" \
    --replication-policy="automatic" \
    --data-file="$FIREBASE_KEY_PATH"
else
  echo "♻️ [ACTUALIZANDO] Secreto '$SECRET_NAME' con nuevo contenido..."
  gcloud secrets versions add "$SECRET_NAME" --data-file="$FIREBASE_KEY_PATH"
fi

# ──────── OTORGAR ACCESO AL SECRETO ────────
echo "🔏 Otorgando acceso a secretos a '$CLOUD_RUN_SA_EMAIL'..."
gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
  --member="serviceAccount:$CLOUD_RUN_SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"

# ──────── PERMISOS PARA CLOUD RUN ────────
echo "🔒 Verificando permisos en Cloud Run..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$CLOUD_RUN_SA_EMAIL" \
  --role="roles/run.invoker" \
  --quiet || true

# ───── VERIFICA STATUS LOCKED FALSE ─────
npm install firebase-admin
node updateLocked.js

# ──────── DESPLIEGUE EN CLOUD RUN ────────
echo "🚀 Desplegando servicio en Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:$TAG" \
  --region="$REGION" \
  --platform=managed \
  --set-env-vars="STORAGE_BUCKET_NAME=$STORAGE_BUCKET_NAME" \
  --set-secrets="/secrets/$SECRET_NAME=${SECRET_NAME}:latest" \
  --allow-unauthenticated \
  --service-account="$CLOUD_RUN_SA_EMAIL" \
  --memory=2Gi

# ──────── ENABLE CLOUD SCHEDULER ────────
echo "🔒 Habilitando API de Cloud Scheduler..."
gcloud services enable cloudscheduler.googleapis.com --project=$PROJECT_ID

# ──────── CREAR JOB DE CLOUD SCHEDULER ────────
echo "🔒 Creando job de Cloud Scheduler..."
DEPLOYED_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format='value(status.url)')

gcloud scheduler jobs create http cronVerifyId \
  --schedule="* * * * *" \
  --uri="$DEPLOYED_URL/cron/verify-id" \
  --http-method=POST \
  --time-zone="America/Los_Angeles" \
  --message-body="{}" \
  --oidc-service-account-email=$CLOUD_RUN_SA_EMAIL \
  --location=$REGION

echo "🌐 Configurando domain mapping $DOMAIN → $SERVICE_NAME..."

gcloud run domain-mappings create \
  --domain="$DOMAIN" \
  --service="$SERVICE_NAME" \
  --region="$REGION" \
  --platform=managed \
  --quiet


echo -e "\n🎉 ✅ ¡Despliegue exitoso de '$SERVICE_NAME' en Cloud Run!"