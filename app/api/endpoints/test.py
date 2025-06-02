from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.services.cron_service import run_cron_verify_id
from app.services.test_service import get_all_users, get_user_by_id
from app.database.config import conect_to_firestoreDataBase
from app.utils.response import create_success_response  

router = APIRouter()

db = conect_to_firestoreDataBase()

@router.get("/get")
def get_data_fake():
    return get_all_users()

@router.get("/get/{user_id}")
def get_user_fake(user_id: int):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.get("/getRequest")
def get_request():
    return run_cron_verify_id()




@router.post("/items")
async def name_post(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Cuerpo de la solicitud no es JSON válido")

    name = body.get("name")
    description = body.get("description")
    price = body.get("price")
    in_stock = body.get("in_stock")

    if not name or not description or price is None or in_stock is None:
        raise HTTPException(status_code=400, detail="Faltan campos requeridos en el cuerpo de la solicitud")

    return {
        "message": "Item recibido correctamente sin Pydantic",
        "name": name,
        "description": description,
        "price": price,
        "in_stock": in_stock
    }
    
    
@router.get("/create")
def create_request_verify_id():
    try:
        request_data = {
            "callback": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "status": "pending",
        }
        
        load_dotenv()  # Cargar 
        storage_bucket_name = os.getenv("STORAGE_BUCKET_NAME")
        print(storage_bucket_name)
        # Crear documento
        doc_ref = db.collection("request").add(request_data)

        if not doc_ref:
            raise HTTPException(status_code=500, detail="No se pudo crear el documento")

        # Obtener ID del documento
        doc_id = doc_ref[1].id

        # Actualizar el mismo documento con su propio ID
        db.collection("request").document(doc_id).update({"id": doc_id})
        
         # Leer documento actualizado
        doc_snapshot = db.collection("request").document(doc_id).get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        doc_data = doc_snapshot.to_dict()
        
         # Convertir datetime a string ISO para JSON
        for key in ["created_at", "updated_at"]:
            if key in doc_data and doc_data[key]:
                doc_data[key] = doc_data[key].isoformat()


        return JSONResponse(create_success_response(data=doc_data , message="Create ", code=200))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
