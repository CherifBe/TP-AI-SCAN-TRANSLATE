from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io

app = FastAPI()

# Configuration CORS pour permettre les requêtes depuis le frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # URL de votre frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # Lire le contenu de l'image
    image_content = await file.read()
    
    # Créer un objet BytesIO pour streamer l'image
    image_stream = io.BytesIO(image_content)
    image_stream.seek(0)
    
    # Retourner l'image en streaming
    return StreamingResponse(
        image_stream,
        media_type=file.content_type,
        headers={"Content-Disposition": f"inline; filename={file.filename}"}
    )