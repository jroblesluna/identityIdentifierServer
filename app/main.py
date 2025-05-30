from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.api.endpoints import test ,recognition
from app.database.config import conect_to_firestoreDataBase
from app.services.database_service import upload_image_cv2
from app.services.recognition_service import read_image_from_url

app = FastAPI()

db = conect_to_firestoreDataBase()

#routes
@app.get("/")
def read_root():
    return {"message": "Hello, from Identity Identifier Server"}

#Test routes , only for testing purpose
app.include_router(test.router, prefix="/test", tags=["test"])
app.include_router(recognition.router, prefix="/recognition", tags=["recognition"])


# # 4. Ruta para guardar el usuario en Firestore
@app.post("/guardar/")
async def guardar_usuario():
    usuario = {"name": "stra", "email": "asd", "age": 1}
    doc_ref = db.collection("usuarios").document()  # colección "usuarios"
    doc_ref.set(usuario)  # guardamos el objeto
    return {"mensaje": "Usuario guardado correctamente", "id": doc_ref.id}


@app.get("/identity/{doc_id}")
def get_identity(doc_id: str):
    doc_ref = db.collection("usuarios").document(doc_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    else:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    
@app.get("/upload/")
def upload():
    cardIdImageUrl = "https://firebasestorage.googleapis.com/v0/b/portafolio-db8bc.appspot.com/o/IMG_20230806_183943.jpg?alt=media&token=cb851317-2f96-4ea8-b22a-a07d483a9538"
    response_card_image_cv2 = read_image_from_url(cardIdImageUrl)
        
    if response_card_image_cv2.get("success") is False:
        return JSONResponse(status_code=response_card_image_cv2.get("code"), content=response_card_image_cv2)
        
    response = upload_image_cv2(response_card_image_cv2.get("data"))
    
    return JSONResponse(status_code=200, content={"message": "Image uploaded successfully", "url": response})