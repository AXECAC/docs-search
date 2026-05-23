from pydantic import BaseModel

class ParseResponse(BaseModel):
  file_id: str
  original_filename: str
  parsed_file_path: str | None = None
  status: str

