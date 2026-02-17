use std::{str::from_utf8, sync::LazyLock};

use infer::Infer;
use mime::{Mime, TEXT_PLAIN};

use crate::errors::ParserError;

type Result<T> = std::result::Result<T, ParserError>;

static INFER: LazyLock<Infer> = LazyLock::new(Infer::new);

/// Определяет MIME файла по считанным данным
pub fn define_mime_type(file_data: &[u8]) -> Option<Mime> {
    if let Some(kind) = INFER.get(file_data)
        && let Ok(mime) = kind.mime_type().parse()
    {
        return Some(mime);
    }

    if from_utf8(file_data).is_ok() {
        return Some(TEXT_PLAIN);
    }

    None
}

fn read_data_from_file(file_name: &str) -> Result<Vec<u8>> {
    Ok(std::fs::read(file_name)?)
}

#[cfg(test)]
mod tests {
    #[test]
    fn define_mime_docx_type() {
        todo!()
    }

    #[test]
    fn define_mime_docx_zip_type() {
        todo!()
    }

    #[test]
    fn define_mime_pdf_type() {
        todo!()
    }

    #[test]
    fn define_mime_pptx_type() {
        todo!()
    }

    #[test]
    fn define_mime_xlsx_type() {
        todo!()
    }

    #[test]
    fn define_mime_text_type() {
        todo!()
    }
}
