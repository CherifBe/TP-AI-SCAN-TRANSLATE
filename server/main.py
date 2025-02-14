import io
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import torch
from ultralytics import YOLO
import pytesseract
from transformers import pipeline
import base64
import textwrap
import locale
locale.getpreferredencoding = lambda: "UTF-8"

pytesseract.pytesseract.tesseract_cmd = "C:\Program Files\Tesseract-OCR\\tesseract.exe"

app = FastAPI()

from textblob import TextBlob
 
def correct_text(text):
    blob = TextBlob(text.lower())
    corrected_text = blob.correct()
    return str(corrected_text)

# Configuration CORS pour permettre les requêtes depuis le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL de votre frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = YOLO("best.pt")
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-fr")

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # Lire le contenu de l'image
    image_bytes = await file.read()
    
    # Convertir les bytes en tableau numpy pour OpenCV
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return {"error": "Impossible de lire l'image."}
    
    # Agrandir l'image avant traitement
    zoom_factor = 3.0
    height, width = img.shape[:2]
    new_height, new_width = int(height * zoom_factor), int(width * zoom_factor)
    img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    
    # Créer une copie pour l'image avec le texte remplacé
    result_image = img.copy()
    
    # Conversion en HSV pour détecter le rouge
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Définition des plages de rouge
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    # Création des masques pour le rouge
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask1, mask2)
    
    # Récupération des contours des zones rouges
    contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    translations_results = []
    
    # Faire les prédictions avec YOLO
    results = model.predict(source=img, conf=0.25)
    
    # Traiter chaque détection
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # Récupérer les coordonnées
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            
            # Extraire la région d'intérêt (ROI)
            roi = img[y1:y2, x1:x2]
            
            # Convertir ROI en niveaux de gris
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Binarisation
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR sur la région
            text = pytesseract.image_to_string(binary, lang="eng+jpn+fra").strip()
            
            # Correction du texte extrait
            if text:
                text = correct_text(text)
            
            # Traduction si du texte est détecté
            if text:
                translation = translator(text, max_length=512)[0]['translation_text']
            else:
                translation = ""
            
            translations_results.append({
                "position": {
                    "x": int(x1),
                    "y": int(y1),
                    "width": int(x2-x1),
                    "height": int(y2-y1)
                },
                "original_text": text,
                "translated_text": translation,
                "confidence": float(conf)
            })
            
            # Dessiner le rectangle sur l'image originale
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, translation[:20] + "..." if len(translation) > 20 else translation,
                       (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Remplacer le texte dans result_image
    for trans in translations_results:
        x = trans["position"]["x"]
        y = trans["position"]["y"]
        w = trans["position"]["width"]
        h = trans["position"]["height"]
        translated_text = trans["translated_text"]
        
        # Effacer la zone d'origine
        cv2.rectangle(result_image, (x, y), (x + w, y + h), (255, 255, 255), -1)
        
        # Paramètres pour l'affichage du texte
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        line_type = cv2.LINE_AA
        
        # Estimer la largeur d'un caractère
        (char_width, char_height), _ = cv2.getTextSize("A", font, font_scale, thickness)
        max_chars_per_line = max(1, w // char_width)
        
        # Découper le texte en lignes
        lines = textwrap.wrap(translated_text, width=max_chars_per_line)
        
        # Calcul de la hauteur totale du texte
        line_spacing = 5
        line_height = char_height + line_spacing
        total_text_height = len(lines) * line_height
        
        # Position de départ pour centrer verticalement
        start_y = y + (h - total_text_height) // 2 + char_height
        
        # Affichage de chaque ligne centrée
        for i, line in enumerate(lines):
            (line_width, _), _ = cv2.getTextSize(line, font, font_scale, thickness)
            text_x = x + (w - line_width) // 2
            text_y = start_y + i * line_height
            cv2.putText(result_image, line, (text_x, text_y), font, font_scale, (0, 0, 0), thickness, line_type)
    
    # Encoder les deux images
    success1, encoded_image1 = cv2.imencode('.jpg', img)
    success2, encoded_image2 = cv2.imencode('.jpg', result_image)
    if not success1 or not success2:
        return {"error": "Erreur lors de l'encodage des images."}
    
    # Convertir les deux images en base64
    image_base64 = base64.b64encode(encoded_image1.tobytes()).decode('utf-8')
    result_image_base64 = base64.b64encode(encoded_image2.tobytes()).decode('utf-8')
    
    return {
        "original_image": f"data:image/jpeg;base64,{image_base64}",
        "translated_image": f"data:image/jpeg;base64,{result_image_base64}",
        "translations": translations_results
    }