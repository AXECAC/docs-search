//! Парсинг docx файлов, а так же и тех которые zip, но по факту docx.

use crate::{
    errors::ParserError,
    parsers::{image::get_from_image, xml::get_info_from_xml_rels},
};
use docx_rs::read_docx;
use std::{collections::HashMap, io::Cursor, path::Path};
use zip::ZipArchive;

type Result<T> = std::result::Result<T, ParserError>;
type Id = String;
type Target = String;

pub(crate) struct DocxParser {
    /// HashMap, где хранятся id картинок и текст извлеченный из них
    pub images: HashMap<Id, String>,
}

impl DocxParser {
    /// Creates a new [`DocxParser`].
    pub(crate) fn new() -> Self {
        Self {
            images: HashMap::new(),
        }
    }

    /// Извлекает текстовые данные из параграфов и таблиц (возможно в будующем и из картинок)
    ///
    /// # Arguments
    /// - `data` - слайс байтов данных из файла
    ///
    /// # Returns
    /// - `Ok(String)` - возвращает текст
    /// - `Err(ParserError::DocxError)` - ошибка во время парсинга файла
    pub(crate) fn get_from_docx(&mut self, data: &[u8]) -> Result<String> {
        let dox = read_docx(data)?;
        // Вытаскиваем все картинки

        // Парсим текст из картинок

        Ok(dox
            .document
            .children
            .iter()
            .filter_map(|from| match from {
                docx_rs::DocumentChild::Paragraph(paragraph) => Some({
                    let mut paragraph_text = self.paragraph_unwrap(paragraph);
                    paragraph_text.push('\n');
                    paragraph_text
                }),
                docx_rs::DocumentChild::Table(table) => Some({
                    let mut table_text = self.table_unwrap(table);
                    table_text.push('\n');
                    table_text
                }),
                _ => None,
            })
            .collect::<Vec<String>>()
            .join("\n")
            .to_string())
    }

    // *****************************************************************************
    // Работа с элементами docx
    // *****************************************************************************

    /// Проходится по всем детям `Paragraph` и извлекает из них текст
    fn paragraph_unwrap(&self, paragraph: &docx_rs::Paragraph) -> String {
        paragraph
            .children
            .iter()
            .filter_map(|from| match from {
                docx_rs::ParagraphChild::Run(run) => Some(self.run_unwrap(run)),
                _ => None,
            })
            .collect::<String>()
    }

    /// Проходится по всем детям `Run` и извлекает из них текст
    fn run_unwrap(&self, run: &docx_rs::Run) -> String {
        run.children
            .iter()
            .filter_map(|from| match from {
                docx_rs::RunChild::Text(text) => Some(text.text.clone()),
                docx_rs::RunChild::Drawing(drawing) => self.drawing_unwrap(drawing).ok()?,
                _ => None,
            })
            .collect::<String>()
    }

    /// Извлекает текст из `Drawing`, если он есть
    fn drawing_unwrap(&self, drawing: &docx_rs::Drawing) -> Result<Option<String>> {
        Ok(match &drawing.data {
            // TODO: реализовать после реализации парсинга картинок
            Some(docx_rs::DrawingData::Pic(pic)) => Some(self.pic_unwrap(pic)?),
            Some(docx_rs::DrawingData::TextBox(text_box)) => Some(self.text_box_unwrap(text_box)),
            _ => None,
        })
    }

    fn pic_unwrap(&self, pic: &docx_rs::Pic) -> Result<String> {
        match self.images.get(&pic.id){
            Some(text) => Ok(text.clone()),
            None => Ok(String::new())
        }
    }

    /// Извлекает текст из `TextBox`
    fn text_box_unwrap(&self, text_box: &docx_rs::TextBox) -> String {
        text_box
            .children
            .iter()
            .map(|from| match from {
                docx_rs::TextBoxContentChild::Paragraph(paragraph) => {
                    self.paragraph_unwrap(paragraph)
                }
                docx_rs::TextBoxContentChild::Table(table) => self.table_unwrap(table),
            })
            .collect::<String>()
    }

    /// Проходится по всем детям `Table` и извлекает из них текст
    fn table_unwrap(&self, table: &docx_rs::Table) -> String {
        table
            .rows
            .iter()
            .map(|from| match from {
                docx_rs::TableChild::TableRow(table_row) => self.table_row_unwrap(table_row),
            })
            .collect::<String>()
    }

    /// Извлекает текст из `TableRow`
    fn table_row_unwrap(&self, table_row: &docx_rs::TableRow) -> String {
        table_row
            .cells
            .iter()
            .map(|from_cell| match from_cell {
                docx_rs::TableRowChild::TableCell(cell) => {
                    let mut cell_text = self.table_cell_unwrap(cell);
                    cell_text.push(' ');
                    cell_text
                }
            })
            .collect::<String>()
    }

    /// Извлекает текст из `TableCell`
    fn table_cell_unwrap(&self, cell: &docx_rs::TableCell) -> String {
        cell.children
            .iter()
            .filter_map(|from_cell_content| match from_cell_content {
                docx_rs::TableCellContent::Table(table) => Some(self.table_unwrap(table)),
                docx_rs::TableCellContent::Paragraph(paragraph) => {
                    Some(self.paragraph_unwrap(paragraph))
                }
                _ => None,
            })
            .collect::<String>()
    }
}
#[cfg(test)]
mod test {

    #[test]
    fn success_extract_media() {}
}
