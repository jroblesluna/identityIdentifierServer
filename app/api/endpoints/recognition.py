from datetime import datetime, timezone
import traceback
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from requests import RequestException
from app.database.config import conect_to_firestoreDataBase
from app.services.database_service import upload_image_cv2
from app.services.recognition_service import compare_verify_faces,  read_image_from_url
from fastapi.responses import JSONResponse
from app.utils.others import convert_numpy_types
from app.utils.response import create_success_response
import time # 👈 for testing porpuse


router = APIRouter()
db = conect_to_firestoreDataBase()


# Endpoint to get one request by ID
@router.get("/get/{request_id}")
def get_request_by_id(request_id: str):
    try:
        doc_ref = db.collection("request").document(request_id)
        doc_snapshot = doc_ref.get()

        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail="Document not found")

        doc_data = doc_snapshot.to_dict()

        for key in ["created_at", "updated_at"]:
            if key in doc_data and isinstance(doc_data[key], datetime):
                doc_data[key] = doc_data[key].isoformat()
                
        return JSONResponse(create_success_response(data=doc_data , message="Document found", code=200))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-id")
async def verify_id_create_Request(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body is not valid JSON")
    
    cardIdImageUrl = body.get("cardIdImageUrl")
    faceImageUrl = body.get("faceImageUrl")
    callback =  body.get("callback")
    
    if not cardIdImageUrl or not faceImageUrl:
         raise HTTPException(status_code=400, detail="Required fields are missing in the body of the request")

    try:
        request_data = {
            "created_at": None ,
            "updated_at": None,
            "status": "pending",
            "success": None,
            "message": None,
            "type": None,
            "data": {
                "input": {
                    "faceImageUrl": None,
                    "cardIdImageUrl": None,
                    "callback": None
                    },
                 "output": None
            }           
        }
        #build the request data
        request_data["data"]["input"]["faceImageUrl"] = faceImageUrl
        request_data["data"]["input"]["cardIdImageUrl"] = cardIdImageUrl
        request_data["data"]["input"]["callback"] = callback
        request_data["type"] = "verify-id"
        request_data["created_at"] = datetime.now(timezone.utc)
        request_data["updated_at"] = datetime.now(timezone.utc)
        
        # Create request
        doc_ref = db.collection("request").add(request_data)

        if not doc_ref:
            raise HTTPException(status_code=500, detail="No se pudo crear el documento")

        # Get document ID
        doc_id = doc_ref[1].id

        load_dotenv()

        # Update the same document with its own ID
        db.collection("request").document(doc_id).update({"id": doc_id , "message": "Request created successfully"})
        
        # Read updated document
        doc_snapshot = db.collection("request").document(doc_id).get()
        if not doc_snapshot.exists:
            raise HTTPException(status_code=404, detail="request not found")

        doc_data = doc_snapshot.to_dict()
        
        # Convert datetime to ISO string for JSON
        for key in ["created_at", "updated_at"]:
            if key in doc_data and doc_data[key]:
                doc_data[key] = doc_data[key].isoformat()


        return JSONResponse(create_success_response(data=doc_data , message="Create request successfully", code=200))

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="error creating request: " + str(e))







    
# /verify-id-test - Sin crear una request en la base de datos, solo resultados
@router.post("/verify-id-test")
async def verify_id_test(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Request body is not valid JSON")
    
    cardIdImageUrl = body.get("cardIdImageUrl")
    faceImageUrl = body.get("faceImageUrl")
    
    if not cardIdImageUrl or not faceImageUrl:
         raise HTTPException(status_code=400, detail="Required fields are missing in the body of the request")
    
    start_time = time.time() # 👈 for testing porpuse
    data_response_compareFace_final ={
        "CardImageCV2": None,
        "FaceImageCV2": None,
        "CardLandMarksImage": None,
        "FaceLandMarksImage": None,
        "distance":0,
        "result_match": False,
    }
     # put in parameters the urls of the images to compare
    
    try:
        response_card_image_cv2 = read_image_from_url(cardIdImageUrl)
        
        # Check if the image card was loaded successfully
        if response_card_image_cv2.get("success") is False:
            return JSONResponse(status_code=response_card_image_cv2.get("code"), content=response_card_image_cv2)
        
        response_face_image_cv2 = read_image_from_url(faceImageUrl)
        
         # Check if the image Face was loaded successfully
        if response_face_image_cv2.get("success") is False:
           return JSONResponse(status_code=response_face_image_cv2.get("code"), content=response_face_image_cv2)
       
        image_card=response_card_image_cv2.get("data")
        face_card=response_face_image_cv2.get("data")
        
        # compare the images
        response_matched=compare_verify_faces(image_card, face_card)    
        
        # Check if the images were compared successfully
        if response_matched.get("success") is False:
            return JSONResponse(status_code=response_matched.get("code"), content=response_matched)
        
             
        elapsed_time_ms = (time.time() - start_time) * 1000  # 👈 for testing porpuse
        print(f"⏱️ Tiempo total de ejecución: {elapsed_time_ms:.2f} ms") # 👈 for testing porpuse
       
        
        # Upload the images to the firebase database
       
        data_compare=response_matched.get("data")
       
        responseUploadCardImage= upload_image_cv2(data_compare.get("CardImageCV2")) 
        
        if responseUploadCardImage.get("success") is False:
            return JSONResponse(status_code=responseUploadCardImage.get("code"), content=responseUploadCardImage)
 
        responseUploadFaceImage= upload_image_cv2(data_compare.get("FaceImageCV2")) 
        
        if responseUploadFaceImage.get("success") is False:
            return JSONResponse(status_code=responseUploadFaceImage.get("code"), content=responseUploadFaceImage)
        
        responseUploadCardLandMark= upload_image_cv2(data_compare.get("CardLandMarksImage")) 
        
        if responseUploadCardLandMark.get("success") is False:
            return JSONResponse(status_code=responseUploadCardLandMark.get("code"), content=responseUploadCardLandMark)        
       
        responseUploadFaceLandMarks= upload_image_cv2(data_compare.get("FaceLandMarksImage")) 
        
        if responseUploadFaceLandMarks.get("success") is False:
            return JSONResponse(status_code=responseUploadFaceLandMarks.get("code"), content=responseUploadFaceLandMarks)        
       
  
        #build the response data
        data_response_compareFace_final["distance"] = data_compare.get("distance") 
        data_response_compareFace_final["result_match"] = data_compare.get("match")
        data_response_compareFace_final["CardImageCV2"] = responseUploadCardImage.get("data")
        data_response_compareFace_final["FaceImageCV2"] = responseUploadFaceImage.get("data")
        data_response_compareFace_final["CardLandMarksImage"] = responseUploadCardLandMark.get("data")
        data_response_compareFace_final["FaceLandMarksImage"] = responseUploadFaceLandMarks.get("data")
        data_response= convert_numpy_types(data_response_compareFace_final)
     
         
        # return the response
        return JSONResponse(create_success_response(data=data_response , message="images successfully compared", code=200))

    except RequestException as e:
        return JSONResponse(status_code=500, content={"Error": f"{str(e)}"})
    
    except TypeError as e:
        print("Error serializing JSON response:", e)
        raise HTTPException(status_code=500, detail="Error processing response")