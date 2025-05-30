import os
from google.cloud import firestore
from pathlib import Path
import firebase_admin # type: ignore
from firebase_admin import credentials, storage # type: ignore
from pathlib import Path

def conect_to_firestoreDataBase():
    """
    Connect to Firestore database using the credentials from the environment variable.
    """
    
    # Make sure the environment variable is set to the project root
    key_path = Path(__file__).resolve().parent.parent.parent / "firebase_key.json"

    print(f"Using Firestore credentials from: {key_path}")
    if not key_path.exists():
        raise FileNotFoundError(f"Firebase key file not found at: {key_path}")
    # Initialize Firestore client
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(key_path)

    db = firestore.Client()

    return db



def connect_to_firestore_storage():
    """
    Connect to Firebase Storage using the credentials from the project root.
    Returns:
        bucket: Firebase Storage bucket instance.
    """
    try:
        # Ruta del archivo de credenciales
        key_path = Path(__file__).resolve().parent.parent.parent / "firebase_key.json"

        # Inicializar Firebase solo si no ha sido inicializado antes
        if not firebase_admin._apps:
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': 'identityidentifierserverqa.firebasestorage.app' # ponerlo en el env
            })

        # Obtener bucket
        bucket = storage.bucket()
        return bucket

    except Exception as e:
        raise RuntimeError(f"Error al conectar con Firebase Storage: {e}")
