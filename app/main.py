from fastapi import FastAPI
from sqlalchemy import text
from app.database import engine
import os

app = FastAPI(title="Document Search API")

@app.on_event("startup")
async def startup():
    try:
        async with engine.connect() as conn:
            # Используем text() для явного указания SQL запроса
            result = await conn.execute(text("SELECT 1"))
            await conn.commit()
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend is running"}

@app.get("/health")
def health():
    return {"status": "healthy", "database_url": os.getenv("DATABASE_URL", "not set")}

"""
import docs_parser
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from schemas import ParseResponse
import os
import uuid

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://0.0.0.0:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/")
def read_item(source: str):
    try:
        # Check if file exists
        if not os.path.exists(source):
            return {"error": f"File not found: {source}"}
        
        # Use extract_text instead of get_text
        # extract_text returns (text_content, images_dict)
        text_content, images = docs_parser.extract_text(source)
        
        return {
            "source": source,
            "text": text_content,
            "has_images": len(images) > 0,
            "image_count": len(images)
        }
    except Exception as e:
        print(f"Error parsing file: {e}")
        return {"error": f"Failed to parse file: {str(e)}"}

@app.post("/upload", response_model=ParseResponse)
async def upload_file(file: UploadFile,
                      parse_immediatly: bool = False):
    file_id = str(uuid.uuid4())
    file_path = f"uploads/raw/{file_id}_{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    parsed_path = None
    parsed_text = None
    
    if parse_immediatly:
        try:
            # Use extract_text to get the content
            text_content, images = docs_parser.extract_text(file_path)
            
            # Save parsed text to a file
            parsed_dir = f"uploads/parsed/{file_id}"
            os.makedirs(parsed_dir, exist_ok=True)
            parsed_path = f"{parsed_dir}/{file.filename}.txt"
            
            with open(parsed_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            
            # Also save images if any
            if images:
                images_dir = f"{parsed_dir}/images"
                os.makedirs(images_dir, exist_ok=True)
                for (page_num, img_num), img_data in images.items():
                    img_path = f"{images_dir}/page_{page_num}_img_{img_num}.png"
                    with open(img_path, "wb") as f:
                        f.write(img_data)
                
        except Exception as e:
            print(f"Parse error: {e}")
            parsed_path = None
    
    return ParseResponse(
        file_id=file_id,
        original_filename=file.filename,
        parsed_file_path=parsed_path,
        status="parsed" if parse_immediatly and parsed_path else "uploaded"
    )

# Optional: Add an endpoint to convert files to new format
@app.post("/convert/{file_id}")
async def convert_file(file_id: str, new_format: str = "txt"):
    # Convert an uploaded file to new format
    # Find the original file
    uploads_dir = "uploads/raw"
    original_file = None
    
    for file in os.listdir(uploads_dir):
        if file.startswith(file_id):
            original_file = os.path.join(uploads_dir, file)
            break
    
    if not original_file:
        return {"error": "File not found"}
    
    try:
        new_path = f"uploads/converted/{file_id}.{new_format}"
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        
        docs_parser.convert_to_new_format(original_file, new_path)
        
        return {
            "file_id": file_id,
            "converted_to": new_format,
            "converted_path": new_path
        }
    except Exception as e:
        return {"error": f"Conversion failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# NOTE: все эти точно работают и работают хорошо
# print(docs_parser.get_text("parser/assets/text_and_tables.docx"))
# print(docs_parser.get_text("parser/assets/some_text.docx"))
# print(docs_parser.get_text("parser/assets/text_tables_png.docx"))
# print(docs_parser.get_text("parser/assets/text_from_img.png"))
# print(docs_parser.get_text("parser/assets/main.typ"))
# print(docs_parser.get_text("parser/assets/main.pdf"))
"""