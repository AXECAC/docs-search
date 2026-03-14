//! Парсинг pdf файлов
//!
//! Для парсинга используется crate-ы pdf_extract

use pdf_extract::extract_text_from_mem;

use crate::errors::ParserError;

type Result<T> = std::result::Result<T, ParserError>;
    type Bytes = u8;

/// Извлекает текстовые данные из pdf
///
/// # Arguments
/// - `data` - слайс байтов данных из файла
///
/// # Returns
/// - Ok([`String`]) - возвращает текст
/// - Err([`ParserError::PdfError`]) - ошибка во время парсинга pdf файла
pub(crate) fn extract_text_from_pdf(data: &[Bytes]) -> Result<String> {
    Ok(extract_text_from_mem(data)?)
}

#[cfg(test)]
mod tests {
    use crate::{errors::ParserError, parsers::pdf::extract_text_from_pdf};

    type Result<T> = std::result::Result<T, ParserError>;
    type Bytes = u8;

    /// Считывает данные из файла ввиде byte vec
    fn read_data_from_file(file_name: &str) -> Result<Vec<Bytes>> {
        Ok(std::fs::read(file_name)?)
    }

    #[test]
    fn extract_from_pdf_file() -> Result<()> {
        let data = read_data_from_file("assets/main.pdf")?;
        let res = extract_text_from_pdf(&data)?;

        assert_eq!(
            res,
            String::from_utf8(read_data_from_file(
                "assets/tests_results/extract_from_pdf_file.txt"
            )?)?
        );
        Ok(())
    }
}
