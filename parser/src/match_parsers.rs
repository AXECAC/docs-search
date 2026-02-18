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

/// Считываем данные из файла ввиде byte vec
fn read_data_from_file(file_name: &str) -> Result<Vec<u8>> {
    Ok(std::fs::read(file_name)?)
}

#[cfg(test)]
mod tests {
    use mime::TEXT_PLAIN;

    use crate::{
        constants::{APPLICATION_DOCX, APPLICATION_DOCX_ZIP, APPLICATION_PDF, APPLICATION_PPTX, APPLICATION_XLS, APPLICATION_XLSX},
        match_parsers::{define_mime_type, read_data_from_file},
    };

    #[test]
    fn define_mime_docx_type() {
        let data = read_data_from_file("assets/возможные вопросы теста.docx").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_DOCX);
    }

    #[test]
    fn define_mime_docx_zip_type() {
        let data = read_data_from_file("assets/6 сем англ.docx").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_DOCX_ZIP);
    }

    #[test]
    fn define_mime_pdf_type() {
        let data = read_data_from_file("assets/matematika._ch.2._tvimst.pdf").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_PDF);
    }

    #[test]
    fn define_mime_pptx_type() {
        let data = read_data_from_file("assets/Презентация_Часть1.pptx").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_PPTX);
    }

    #[test]
    fn define_mime_xls_type() {
        let data = read_data_from_file("assets/Сроки_зимней_сессии_и_пересдач_25_26.xls").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_XLS);
    }

    #[test]
    fn define_mime_xlsx_type() {
        let data = read_data_from_file("assets/Book.xlsx").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_XLSX);
    }

    #[test]
    fn define_mime_text_type() {
        let data = read_data_from_file("assets/main.typ").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), TEXT_PLAIN);
    }
}
