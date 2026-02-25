//! Парсинг текстовых файлов
//!

use crate::errors::ParserError;

type Result<T> = std::result::Result<T, ParserError>;

/// Парсит байты текстового файла в текст
///
/// # Arguments
/// - `data` - слайс байтов данных из файла
///
/// # Returns
/// - Ok([`String`]) - возвращает текст
/// - Err([`ParserError`]) - ошибка во время парсинга байтов текстового файла
pub(crate) fn get_from_text(data: &[u8]) -> Result<String> {
    Ok(String::from_utf8(data.to_vec())?)
}

