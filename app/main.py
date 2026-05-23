import docs_parser
from fastapi import FastAPI, File, UploadFile
from schemas import ParseResponse
import os
import uuid
app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/")
def read_item(source: str):
    return {source: docs_parser.get_text(source)}

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
    return ParseResponse(
        file_id=file_id,
        original_filename=file.filename,
        parsed_file_path=parsed_path,
        status = "parsed" if parse_immediatly else "uploaded"
    )


# NOTE: все эти точно работают и работают хорошо
# print(docs_parser.get_text("parser/assets/text_and_tables.docx"))
# print(docs_parser.get_text("parser/assets/some_text.docx"))
# print(docs_parser.get_text("parser/assets/text_tables_png.docx"))
# print(docs_parser.get_text("parser/assets/text_from_img.png"))
# print(docs_parser.get_text("parser/assets/main.typ"))
# print(docs_parser.get_text("parser/assets/main.pdf"))
