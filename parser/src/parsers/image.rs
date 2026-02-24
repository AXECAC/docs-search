//! Парсинг картинок формата PNG, JPEG и т.д

use crate::{errors::ParserError, match_parsers};
use mime::{IMAGE_BMP, IMAGE_JPEG, IMAGE_PNG, Mime};
use std::io::{Cursor, Write};
use tempfile::NamedTempFile;
use tesseract::Tesseract;

type Result<T> = std::result::Result<T, ParserError>;

/// Парсит байты картинки и извлекает из них текст используя OCR
///
/// Эта функция принимает сырые байты картинки и используя Tesseract OCR
/// извлекает любой текст с картинки
///
/// # Arguments
///
/// - `data` - Слайс содержащий байты картинки (PNG, JPEG, etc.)
///
/// # Returns
///
/// - `Ok(String)` - ивзлеченный текст из картинки
/// - `Err(ParserError)` - ошибка во время парсинга или обработки картинки
///
/// # Errors
/// - [`ParserError::IoTempFileError`] - ошибка во время создания temp файла
/// - [`ParserError::ImageError`] - ошибка во время обработки картинки
/// - Остальные [`ParserError`] связанные с Tesseract ошибки во время парсинга картинки
///
/// # Implementation Notes
///
/// - Используется Tesseract OCR с поддержкой Английского и русского языка
/// - Создается временный файл для передачи его в Tesseract
pub(crate) fn get_from_image(data: &[u8]) -> Result<String> {
    let valid_data = match match_parsers::define_mime_type(data) {
        Some(mime) if is_correct_img_mime(&mime) => data,
        _ => &convert_to_png(data)?,
    };

    // Создаем временный файл, для использования в OCR
    let mut temp_file = NamedTempFile::new()?;
    temp_file.write_all(valid_data)?;

    let temp_file_path = temp_file
        .path()
        .to_str()
        .ok_or_else(|| ParserError::IoTempFileError("".to_string()))?;

    Ok(parse_with_tesseract(temp_file_path)?.trim_end().to_string())
}

/// Проверка: является ли MIME тип поддерживаемым для парсинга
fn is_correct_img_mime(mime: &Mime) -> bool {
    *mime == IMAGE_PNG || *mime == IMAGE_JPEG || *mime == IMAGE_BMP
}

/// Попытка конвертировать байты катинки в png для дальнейшего парсинга
fn convert_to_png(data: &[u8]) -> Result<Vec<u8>> {
    let img = image::load_from_memory(data)?;
    let mut buf = Cursor::new(Vec::new());
    img.write_to(&mut buf, image::ImageFormat::Png)?;

    Ok(buf.into_inner())
}

/// Распознавание текста с помощью Tesseract OCR
///
/// # Arguments
///
/// - `path` - путь до файла с картинкой
///
/// # Returns
///
/// - `Ok(String)` - извлеченный текст
/// - `Err(ParserError)` - если при работе с Tesseract возникает ошибка
fn parse_with_tesseract(path: &str) -> Result<String> {
    // Инициализируем Tesseract с Английским и Русским языками
    let tes = Tesseract::new(None, Some("eng+rus"))?;

    Ok(tes.set_image(path)?.get_text()?)
}
