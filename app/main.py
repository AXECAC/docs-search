import docs_parser
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/")
def read_item(source: str):
    return {source: docs_parser.get_text(source)}

# NOTE: все эти точно работают и работают хорошо
# print(docs_parser.get_text("parser/assets/text_and_tables.docx"))
# print(docs_parser.get_text("parser/assets/some_text.docx"))
# print(docs_parser.get_text("parser/assets/text_tables_png.docx"))
# print(docs_parser.get_text("parser/assets/text_from_img.png"))
# print(docs_parser.get_text("parser/assets/main.typ"))
# print(docs_parser.get_text("parser/assets/main.pdf"))
