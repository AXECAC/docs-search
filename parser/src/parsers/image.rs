use crate::errors::ParserError;
use std::io::Write;
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
/// - `Ok(String)` - The extracted text from the image
/// - `Err(ParserError)` - If an error occurs during image processing or OCR
///
/// # Implementation Notes
///
/// - Используется Tesseract OCR с поддержкой Английского и русского языка
/// - Создается временный файл для передачи его в Tesseract
pub(crate) fn get_from_image(data: &[u8]) -> Result<String> {
    // Создаем временный файл, для использования в OCR
    let mut temp_file = NamedTempFile::new()?;
    temp_file.write_all(data)?;

    let temp_file_path = temp_file
        .path()
        .to_str()
        .ok_or_else(|| ParserError::IoTempFileError("".to_string()))?;

    todo!()
}

