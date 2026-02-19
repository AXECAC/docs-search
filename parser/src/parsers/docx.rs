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
            docx_rs::DocumentChild::Paragraph(paragraph) => Some(paragraph_unwrap(paragraph)),
            docx_rs::DocumentChild::Table(table) => todo!(),
            _ => None,
        })
        .collect::<Vec<String>>()
        .join("\n")
        .to_string())
}

/// Проходится по всем детям `Paragraph` и извлекает из них текст
fn paragraph_unwrap(paragraph: &docx_rs::Paragraph) -> String {
    paragraph
        .children
        .iter()
        .filter_map(|from| match from {
            docx_rs::ParagraphChild::Run(run) => Some(run_unwrap(run)),
            _ => None,
        })
        .collect::<String>()
}

/// Проходится по всем детям `Run` и извлекает из них текст
fn run_unwrap(run: &docx_rs::Run) -> String {
    run.children
        .iter()
        .filter_map(|from| match from {
            docx_rs::RunChild::Text(text) => Some(text.text.clone()),
            docx_rs::RunChild::Drawing(drawing) => todo!(),
            _ => None,
        })
        .collect::<String>()
}
