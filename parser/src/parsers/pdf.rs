//! Парсинг pdf файлов
//!
//! Для парсинга используется crate-ы pdf_extract

use pdf_extract::extract_text_from_mem;

use crate::errors::ParserError;

type Result<T> = std::result::Result<T, ParserError>;

pub(crate) fn get_from_pdf(data: &[u8]) -> Result<String> {
    Ok(extract_text_from_mem(data)?)
}
