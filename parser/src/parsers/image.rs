//! Парсинг картинок формата PNG, JPEG и т.д
//!
//! Для парсинга используется crate tesseract

use crate::{errors::ParserError, match_parsers};
use mime::{IMAGE_BMP, IMAGE_JPEG, IMAGE_PNG, Mime};
use std::io::Cursor;
use tesseract::Tesseract;

type Result<T> = std::result::Result<T, ParserError>;

/// Парсит байты картинки и извлекает из них текст используя OCR
///
/// Эта функция принимает сырые байты картинки и используя Tesseract OCR
/// извлекает любой текст с картинки
///
/// # Arguments
/// - `data` - Слайс содержащий байты картинки (PNG, JPEG, etc.)
///
/// # Returns
/// - Ok([`String`]) - ивзлеченный текст из картинки
/// - Err([`ParserError`]) - ошибка во время парсинга или обработки картинки
///
/// # Errors
/// - [`ParserError::ImageError`] - ошибка во время обработки картинки
/// - Остальные [`ParserError`] связанные с Tesseract ошибки во время парсинга картинки
pub(crate) fn get_from_image(data: &[u8]) -> Result<String> {
    let valid_data = match match_parsers::define_mime_type(data) {
        Some(mime) if is_correct_img_mime(&mime) => data,
        _ => &convert_to_png(data)?,
    };

    Ok(parse_with_tesseract(valid_data)?.trim_end().to_string())
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
/// - `path` - путь до файла с картинкой
///
/// # Returns
/// - Ok([`String`]) - извлеченный текст
/// - Err([`ParserError`]) - если при работе с Tesseract возникает ошибка
fn parse_with_tesseract(data: &[u8]) -> Result<String> {
    // Инициализируем Tesseract с Английским и Русским языками
    let tes = Tesseract::new(None, Some("eng+rus"))?;

    Ok(tes.set_image_from_mem(data)?.get_text()?)
}

#[cfg(test)]
mod tests {
    use crate::{errors::ParserError, parsers::image::get_from_image};

    type Result<T> = std::result::Result<T, ParserError>;

    /// Считывает данные из файла ввиде byte vec
    fn read_data_from_file(file_name: &str) -> Result<Vec<u8>> {
        Ok(std::fs::read(file_name)?)
    }

    #[test]
    fn extract_from_image_en() -> Result<()> {
        let data = read_data_from_file("assets/text_from_img_en.png")?;
        let res = get_from_image(&data)?;

        assert_eq!(
            res.trim(),
            String::from_utf8(read_data_from_file(
                "assets/tests_results/extract_from_image_en.txt"
            )?)?
            .trim()
        );
        Ok(())
    }

    #[test]
    fn extract_from_image_ru() -> Result<()> {
        let data = read_data_from_file("assets/text_from_img_ru.png")?;
        let res = get_from_image(&data)?;

        assert_eq!(
            res.trim(),
            String::from_utf8(read_data_from_file(
                "assets/tests_results/extract_from_image_ru.txt"
            )?)?
            .trim()
        );
        Ok(())
    }
}
