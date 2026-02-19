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
            docx_rs::RunChild::Drawing(drawing) => drawing_unwrap(drawing),
            _ => None,
        })
        .collect::<String>()
}

/// Извлекает текст из `Drawing`, если он есть
fn drawing_unwrap(drawing: &docx_rs::Drawing) -> Option<String> {
    match &drawing.data {
        // TODO: реализовать после реализации парсинга картинок
        Some(docx_rs::DrawingData::Pic(pic)) => todo!(),
        Some(docx_rs::DrawingData::TextBox(text_box)) => Some(text_box_unwrap(text_box)),
        _ => None,
    }
}

/// Извлекает текст из `TextBox`
fn text_box_unwrap(text_box: &docx_rs::TextBox) -> String {
    text_box
        .children
        .iter()
        .filter_map(|from| match from {
            docx_rs::TextBoxContentChild::Paragraph(paragraph) => Some(paragraph_unwrap(paragraph)),
            docx_rs::TextBoxContentChild::Table(table) => todo!(),
        })
        .collect::<String>()
}
