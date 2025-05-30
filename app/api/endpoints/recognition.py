import logging
from fastapi import APIRouter, HTTPException
from requests import RequestException
from app.services.database_service import upload_image_cv2
from app.services.recognition_service import compare_verify_faces, load_image_cv, read_image_from_url, resize_image
from fastapi.responses import JSONResponse
import time # 👈 for testing porpuse
from app.utils.others import convert_numpy_types
from app.utils.response import create_success_response

router = APIRouter()


    

@router.get("/verify-id")
def verify_id():
    start_time = time.time() # 👈 for testing porpuse
    data_response_compareFace_final ={
        "CardImageCV2": None,
        "FaceImageCV2": None,
        "CardLadnMarksImage": None,
        "FaceLandMarksImage": None,
        "distance":0,
        "result_match": False,
    }
    cardIdImageUrl = "https://firebasestorage.googleapis.com/v0/b/portafolio-db8bc.appspot.com/o/IMG_20230806_183943.jpg?alt=media&token=cb851317-2f96-4ea8-b22a-a07d483a9538"
    faceImageUrl ="https://firebasestorage.googleapis.com/v0/b/portafolio-db8bc.appspot.com/o/IMG_20230415_173655.jpg?alt=media&token=c79ba8e1-cb66-4315-8902-168e759eaedc"
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
        
        # Upload the images to the firebase database
       
        data_compare=response_matched.get("data")
       
        responseUploadCardImage= upload_image_cv2(data_compare.get("CardImageCV2")) 
        
        if responseUploadCardImage.get("success") is False:
            return JSONResponse(status_code=responseUploadCardImage.get("code"), content=responseUploadCardImage)
 
        responseUploadFaceImage= upload_image_cv2(data_compare.get("FaceImageCV2")) 
        
        if responseUploadFaceImage.get("success") is False:
            return JSONResponse(status_code=responseUploadFaceImage.get("code"), content=responseUploadFaceImage)
        
        responseUploadCardLandMark= upload_image_cv2(data_compare.get("CardLadnMarksImage")) 
        
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
        data_response_compareFace_final["CardLadnMarksImage"] = responseUploadCardLandMark.get("data")
        data_response_compareFace_final["FaceLandMarksImage"] = responseUploadFaceLandMarks.get("data")
        data_response= convert_numpy_types(data_response_compareFace_final)
     
        elapsed_time_ms = (time.time() - start_time) * 1000  # 👈 for testing porpuse
        print(f"⏱️ Tiempo total de ejecución: {elapsed_time_ms:.2f} ms") # 👈 for testing porpuse
         
        # return the response
        return JSONResponse(create_success_response(data=data_response , message="images successfully compared", code=200))

    except RequestException as e:
        return JSONResponse(status_code=500, content={"Error": f"{str(e)}"})
    
    except TypeError as e:
        logging.exception("Error serializing JSON")
        raise HTTPException(status_code=500, detail="Error processing response")