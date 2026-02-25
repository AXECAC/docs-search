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
/// - Err([`ParserError::FromUTF8Error`]) - ошибка во время парсинга байтов текстового файла
pub(crate) fn get_from_text(data: &[u8]) -> Result<String> {
    Ok(String::from_utf8(data.to_vec())?)
}

#[cfg(test)]
mod tests {
    use crate::{errors::ParserError, parsers::text::get_from_text};

    type Result<T> = std::result::Result<T, ParserError>;

    /// Считывает данные из файла ввиде byte vec
    fn read_data_from_file(file_name: &str) -> Result<Vec<u8>> {
        Ok(std::fs::read(file_name)?)
    }

    #[test]
    fn extract_from_txt_file() -> Result<()> {
        let data = read_data_from_file("assets/main.typ")?;
        let res = get_from_text(&data)?;
        assert_eq!(
            res,
            String::from_utf8(read_data_from_file(
                "assets/tests_results/extract_from_txt_file.txt"
            )?)?
        );
        Ok(())
    }
}
