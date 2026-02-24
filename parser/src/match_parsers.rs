//! Функции определения MIME и выбора парсера в зависимости от MIME

use std::{str::from_utf8, sync::LazyLock};

use infer::Infer;
use mime::{IMAGE, Mime, TEXT, TEXT_PLAIN};

use crate::{
    constants::{
        APPLICATION_DOCX, APPLICATION_DOCX_ZIP, APPLICATION_PDF, APPLICATION_PPTX, APPLICATION_RTF,
        APPLICATION_XLS, APPLICATION_XLSX,
    },
    errors::ParserError,
    parsers::{docx, image::get_from_image},
};

type Result<T> = std::result::Result<T, ParserError>;

static INFER: LazyLock<Infer> = LazyLock::new(Infer::new);

/// Извлекает текст из файла
/// # Arguments
/// - `file_name` - название файла, из которого нужно извлечь текст
///
/// # Returns
/// - `Ok(String)` - возвращает текст
/// - `Err(ParserError)` - если тип файла не поддерживается, не определен или
///   какая-то другая ошибка
///
/// # Errors
/// - `[ParserError::InvalidFormat]` - тип файла не поддерживается/не определен
/// - Остальные варианты `[ParserError]`, если ошибка во время парсинга файла
pub fn get_text(file_name: &str) -> Result<String> {
    let file_data = read_data_from_file(file_name)?;
    match define_mime_type(&file_data) {
        Some(mime)
            if mime == APPLICATION_DOCX
                || (mime == APPLICATION_DOCX_ZIP && file_name.contains(".docx")) =>
        {
            let mut docx_parser = docx::DocxParser::new();
            docx_parser.get_from_docx(&file_data)
        }
        Some(mime) if mime == APPLICATION_XLSX => todo!(),
        Some(mime) if mime == APPLICATION_PPTX => todo!(),
        Some(mime) if mime == APPLICATION_PDF => todo!(),
        Some(mime) if mime.type_() == TEXT => todo!(),
        Some(mime) if mime.type_() == IMAGE => get_from_image(&file_data),
        Some(mime) if is_converted_mime_type(&mime) => Err(ParserError::InvalidFormat(format!(
            "Не поддерживается данный тип файла {mime}, но его вы можете конвертировать \
            в поддерживаемый формат через отдельный метод конвертации"
        ))),
        Some(mime) => Err(ParserError::InvalidFormat(format!(
            "Не поддерживается данный тип файла {mime}"
        ))),
        None => Err(ParserError::InvalidFormat(
            "Не получается определить данный тип файла ".to_string(),
        )),
    }
}

/// Проверка: является ли данный MIME конвертируемым в поддерживаемые MIME
fn is_converted_mime_type(mime: &Mime) -> bool {
    *mime == APPLICATION_RTF || *mime == APPLICATION_XLS
}

/// Определяет MIME файла по считанным данным
///
/// # Arguments
/// - `file_data` - слайс содержащий данные из файла, использующиеся для анализа
///
/// # Returns
/// - `Some(mime)` - тип MIME определен
/// - `None` - тип MIME не был определен
pub(crate) fn define_mime_type(file_data: &[u8]) -> Option<Mime> {
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

/// Считывает данные из файла ввиде byte vec
fn read_data_from_file(file_name: &str) -> Result<Vec<u8>> {
    Ok(std::fs::read(file_name)?)
}

#[cfg(test)]
mod tests {
    use mime::TEXT_PLAIN;

    use crate::{
        constants::{
            APPLICATION_DOCX, APPLICATION_DOCX_ZIP, APPLICATION_PDF, APPLICATION_PPTX,
            APPLICATION_XLSX,
        },
        match_parsers::{define_mime_type, read_data_from_file},
    };

    #[test]
    fn define_mime_docx_type() {
        let data = read_data_from_file("assets/text_and_tables.docx").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_DOCX);
    }

    #[test]
    fn define_mime_docx_zip_type() {
        let data = read_data_from_file("assets/some_text.docx").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_DOCX_ZIP);
    }

    #[test]
    fn define_mime_pdf_type() {
        let data = read_data_from_file("assets/main.pdf").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_PDF);
    }

    #[test]
    fn define_mime_pptx_type() {
        let data = read_data_from_file("assets/Presentation.pptx").unwrap();
        let mime = define_mime_type(&data);
        assert!(mime.is_some());
        assert_eq!(mime.unwrap(), APPLICATION_PPTX);
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
