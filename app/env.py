import os
from dotenv import load_dotenv

# Solo carga .env si no estás en producción
if os.getenv("ENV", "local") != "production":
    load_dotenv()

STORAGE_BUCKET_NAME = os.getenv("STORAGE_BUCKET_NAME")