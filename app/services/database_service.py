import cv2
import uuid
from app.database.config import connect_to_firestore_storage
from app.utils.response import create_error_response, create_success_response
from firebase_admin import  storage # type: ignore

bucket=connect_to_firestore_storage()



def upload_image_cv2(frame) -> str:
    try:
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_bytes = img_encoded.tobytes()

        filename = f"{uuid.uuid4()}.jpg"
        token = str(uuid.uuid4())

        bucket = storage.bucket()
        blob = bucket.blob(f"images/{filename}")

        # Add token as metadata to generate Firebase-like URLs
        blob.metadata = {"firebaseStorageDownloadTokens": token}
        blob.upload_from_string(img_bytes, content_type='image/jpeg')
        blob.patch()  # Required to apply metadata

        # Build the link manually
        url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/images%2F{filename}?alt=media&token={token}"

        return create_success_response(url, message="Image uploaded successfully", code=200)

    except Exception as e:
        print(f"An error occurred during image upload: {e}")
        return create_error_response(code=500, message=f"An error occurred during image upload: {str(e)}")
