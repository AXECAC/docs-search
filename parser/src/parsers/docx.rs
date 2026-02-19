//! Парсинг docx файлов. (возможно и тех которые zip, но по факту docx)

use docx_rs::read_docx;

use crate::errors::ParserError;

type Result<T> = std::result::Result<T, ParserError>;

/// Извлекает текстовые данные из параграфов и таблиц (возможно в будующем и из картинок)
/// # Arguments
/// - `data` - слайс байтов данных из файла
///
/// # Returns
/// - `Ok(String)` - возвращает текст
/// - `Err(ParserError::DocxError)` - ошибка во время парсинга файла
pub(crate) fn get_from_docx(data: &[u8]) -> Result<String> {
    let dox = read_docx(data)?;

    Ok(dox
        .document
        .children
        .iter()
        .filter_map(|from| match from {
            docx_rs::DocumentChild::Paragraph(paragraph) => todo!(),
            docx_rs::DocumentChild::Table(table) => todo!(),
            _ => None,
        })
        .collect::<Vec<String>>()
        .join("\n")
        .to_string())
}

