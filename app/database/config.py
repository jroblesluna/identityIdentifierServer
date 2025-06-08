import os
from google.cloud import firestore
from pathlib import Path
import firebase_admin  # type: ignore
from firebase_admin import credentials, storage  # type: ignore

# Carga .env solo en entorno local
if os.getenv("ENV", "local") != "production":
    from dotenv import load_dotenv
    load_dotenv()

# Usa variable global para evitar múltiples inicializaciones
_firebase_initialized = False


def get_firebase_key_path() -> Path:
    """
    Devuelve la ruta del archivo firebase_key.json.
    En Cloud Run, usa el secreto montado en /secrets/FIREBASE_KEY.
    Localmente, usa firebase_key.json o FIREBASE_KEY_PATH.
    """
    cloud_run_path = Path("/secrets/FIREBASE_KEY")
    if cloud_run_path.exists():
        return cloud_run_path

    # Fallback a variable de entorno o ruta por defecto local
    return Path(os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")).resolve()


def conect_to_firestoreDataBase():
    """
    Conectar a Firestore con GOOGLE_APPLICATION_CREDENTIALS.
    """
    key_path = get_firebase_key_path()

    if not key_path.exists():
        raise FileNotFoundError(f"Firebase key file not found at: {key_path}")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_path)
    return firestore.Client()


def connect_to_firestore_storage():
    """
    Conectar a Firebase Storage usando el archivo de credenciales.
    Retorna el bucket configurado.
    """
    global _firebase_initialized

    key_path = get_firebase_key_path()

    if not key_path.exists():
        raise FileNotFoundError(f"Firebase key file not found at: {key_path}")

    storage_bucket_name = os.getenv("STORAGE_BUCKET_NAME")
    if not storage_bucket_name:
        raise ValueError("La variable de entorno STORAGE_BUCKET_NAME no está definida")

    if not _firebase_initialized:
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': storage_bucket_name
        })
        _firebase_initialized = True

    return storage.bucket()