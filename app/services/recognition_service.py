import time
from PIL import Image
import face_recognition
import cv2
from fastapi import HTTPException
from fastapi.responses import JSONResponse
import numpy as np
import requests
import traceback
from app.services.database_service import upload_image_cv2
from app.utils.others import convert_numpy_types
from app.utils.response import create_error_response, create_success_response


PREPROCESS = True
RESIZE = True
DRAW_RECTANGLE = False
THRESHOLD_RECOGNITION=0.6




def draw_landmarks(image , face_locations=None):
    
    if face_locations is None:
      if not isinstance(image, np.ndarray):
        image = np.array(image)
      if image.dtype != np.uint8:
        image = image.astype(np.uint8)
      if not image.flags.writeable:
        image = image.copy()

      landmarks_list = face_recognition.face_landmarks(image)
      if(len(landmarks_list) == 0):
         print("No landmarks found in the image.")
       
      for landmarks in landmarks_list:
            for points in landmarks.values():
                for point in points:
                    cv2.circle(image, point, 1, (0, 255, 0), -1)
    else:
        for face_location in face_locations:
            landmarks_list = face_recognition.face_landmarks(image, [face_location])
            for landmarks in landmarks_list:
                for points in landmarks.values():
                    for point in points:
                        cv2.circle(image, point, 1, (0, 255, 0), -1)
    return image
def detect_faces(image):
    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=15)
    min_area = 2000
    return [face for face in faces if face[2] * face[3] >= min_area]


def capture_face(frame):
    global PREPROCESS, RESIZE, DRAW_RECTANGLE  # declarar uso de variables globales

    face_crop_found = []
    image_np = load_image_cv(frame)

    if PREPROCESS:
        image_np = preprocess_image(image_np)

    # Convertir a BGR y redimensionar si es necesario
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    if RESIZE:
        image_bgr = resize_image(image_bgr)

    faces = detect_faces(image_bgr)
    height, width, _ = image_bgr.shape
    margin = 20

    if DRAW_RECTANGLE:
        for (x, y, w, h) in faces:
            cv2.rectangle(image_bgr, (x, y), (x + w, y + h), (0, 0, 255), 4)

    if faces:
        for (x, y, w, h) in faces:
            x1 = max(x - margin, 0)
            y1 = max(y - margin, 0)
            x2 = min(x + w + margin, width)
            y2 = min(y + h + margin, height)

            face_crop = image_bgr[y1:y2, x1:x2][:, :, ::-1]
            face_crop_found.append(face_crop)
    else:
        print("No face detected in the uploaded identity image.")

    return image_np, image_bgr, face_crop_found


def resize_image(image, max_size=600):
    h, w = image.shape[:2]
    if max(h, w) > max_size:
        scale = max_size / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        return cv2.resize(image, (new_w, new_h))
    return image

def load_image_cv(image_file):
    if isinstance(image_file, Image.Image):
        return cv2.cvtColor(np.array(image_file), cv2.COLOR_RGB2BGR)
    elif isinstance(image_file, np.ndarray):
        return cv2.cvtColor(image_file, cv2.COLOR_BGR2RGB)
    else:
        image_file.seek(0)
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        return cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)


def fast_denoise(image: np.ndarray, ksize: int = 3) -> np.ndarray:
    return cv2.GaussianBlur(image, (ksize, ksize), 0)

def sharpen_image(image: np.ndarray, strength: float =0.2) -> np.ndarray:
    """
    Aumenta la nitidez de la imagen aplicando un filtro de convolución.

    Parámetros:
    - image: Imagen de entrada como np.ndarray.
    - strength: Multiplicador para controlar cuán fuerte es el efecto de nitidez (default 1.0).

    Retorna:
    - Imagen con mayor nitidez.
    """
    # Kernel base de sharpening
    kernel = np.array([[0, -1, 0],
                       [-1, 5 + 4*(strength - 1), -1],
                       [0, -1, 0]])
    return cv2.filter2D(image, -1, kernel)

def adjust_contrast_brightness(image: np.ndarray, alpha: float = 1.5, beta: int = 20) -> np.ndarray:
    """
    Ajusta el contraste y brillo de la imagen.

    Parámetros:
    - image: Imagen de entrada como np.ndarray.
    - alpha: Factor de contraste. 1.0 = sin cambio, >1 aumenta contraste.
    - beta: Valor de brillo agregado. 0 = sin cambio, >0 ilumina.

    Retorna:
    - Imagen modificada con nuevo contraste y brillo.
    """
    return cv2.convertScaleAbs(image, alpha=alpha, beta=beta)


def apply_clahe(image: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    if len(image.shape) == 3 and image.shape[2] == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l2 = clahe.apply(l)
        lab = cv2.merge((l2, a, b))
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    else:
        return clahe.apply(image)

def equalize_histogram(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 3 and image.shape[2] == 3:
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
        return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    else:
        return cv2.equalizeHist(image)


def preprocess_image(image: np.ndarray) -> np.ndarray:
    image = fast_denoise(image)
    #image = apply_clahe(image)
    #image = sharpen_image(image) #  a lot failed
    #image = adjust_contrast_brightness(image, alpha=1.5, beta=10)
    return image


def read_image_from_url(url: str):
    
    """
    Downloads an image from a URL and converts it to a format suitable for OpenCV.

    Parameters:
    - url: Image URL.

    Returns:
    - Image as np. ndarray.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Throws error if the response is not 200
        
          # Convert bytes to an OpenCV image
        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        
        if image is None:
            return create_error_response(code=400, message="The image could not be decoded.")
          #  return JSONResponse(status_code=400, content={"error": "The image could not be decoded.."})

        return create_success_response(data=image, message="Image downloaded successfully", code=200)
        
        
    except requests.RequestException as e:
        return create_error_response(code=500, message=f"Error downloading image or invalid image -  {str(e)}")
      #  return JSONResponse(status_code=500, content={"error": f"Error downloading image or invalid image: {str(e)}"})  
    

    
    
def compare_verify_faces(image1: np.ndarray, image2: np.ndarray) : 
    """
    image1 = ID card image
    image2 = Face image
    """
    try:
            
        data_response_compare ={
            "CardImageCV2": None,
            "FaceImageCV2": None,
            "CardLandMarksImage": None,
            "FaceLandMarksImage": None,
            "distance": None,
            "match": None,
        }

        
        data_response_compare["CardImageCV2"] = image1
        data_response_compare["FaceImageCV2"] = image2
        
        
        _, _, face_crop_found_card = capture_face( image1)
        _, _, face_crop_found_face = capture_face(image2)

        img1_resized =  resize_image(load_image_cv(image1)) #ID CARD
        img1_resized =preprocess_image(img1_resized)
        img2_resized= resize_image(load_image_cv(image2)) # FACE UPLOAD
        img2_resized = preprocess_image(img2_resized)
        enc1=None
        enc2=None
        face_locations1= None
        face_locations2= None
        
        if len( face_crop_found_card) >0:
            enc1 = face_recognition.face_encodings(load_image_cv(face_crop_found_card[0]))

        elif len(face_recognition.face_encodings(img1_resized)) ==0 :
            face_locations1 = face_recognition.face_locations(img1_resized, model= "cnn")
            if len(face_locations1) >0:
                enc1 = face_recognition.face_encodings(img1_resized, known_face_locations=[face_locations1[0]])
                print("No face detected in the uploaded ID image - CNN")
            else:
                enc1 = face_recognition.face_encodings(img1_resized)
        else: 
            enc1 = face_recognition.face_encodings(img1_resized)           
            

        if len(face_crop_found_face) > 0:
            enc2 = face_recognition.face_encodings(load_image_cv(face_crop_found_face[0]))
        elif len(face_recognition.face_encodings(img2_resized)) == 0 :
            face_locations2 = face_recognition.face_locations(img2_resized, model= "cnn")
            if len(face_locations2) >0:
                enc2 = face_recognition.face_encodings(img2_resized, known_face_locations=[face_locations2[0]])
                print("No face detected in the uploaded face image - CNN")
            else:
                enc2 = face_recognition.face_encodings(img2_resized)
        else:
            enc2 = face_recognition.face_encodings(img2_resized)
            
        # Put Landmarks on the images
           
        if len(face_crop_found_card) > 0:
            data_response_compare["CardLandMarksImage"] = draw_landmarks(face_crop_found_card[0].copy())[:, :, ::-1]
        elif enc1:
            data_response_compare["CardLandMarksImage"] =draw_landmarks(img1_resized.copy(), face_locations1)[:, :, ::-1] 
        else:
            data_response_compare["CardLandMarksImage"] = None
        
        
        if len(face_crop_found_face) > 0:
            data_response_compare["FaceLandMarksImage"] = draw_landmarks(face_crop_found_face[0].copy())[:, :, ::-1]
        elif enc1:
            data_response_compare["FaceLandMarksImage"] =draw_landmarks(img2_resized.copy(), face_locations2)[:, :, ::-1] 
        else:
            data_response_compare["FaceLandMarksImage"] = None
        
            

        errors = []

        if not enc1:
            errors.append("No face found in identity card. (1)")

        if not enc2:
            errors.append("No face found in captured/uploaded photo. (2)")

        if errors:
            return create_error_response(
                code=400,
                message="; ".join(errors),
                data=data_response_compare
            )
            
        else:
             match = face_recognition.compare_faces([enc1[0]], enc2[0] ,tolerance=THRESHOLD_RECOGNITION)[0]
             distance = face_recognition.face_distance([enc1[0]], enc2[0] )[0]
             
             data_response_compare["distance"] = distance
             data_response_compare["match"] = match
             
             
             return create_success_response(data=data_response_compare, message="Images compared successfully", code=200)
          
    except Exception as e:
        print(traceback.format_exc())
        return create_error_response(code=500, message=f"Error processing images: {str(e)}")
    
    
    
    
    
    
