//! Парсинг docx файлов, а так же и тех которые zip, но по факту docx.
//!
//! Для парсинга используется crate-ы docx_rs и zip

use crate::{
    errors::ParserError,
    parsers::{image::get_from_image, xml::get_info_from_xml_rels},
};
use rayon::prelude::*;

use docx_rs::read_docx;
use quick_xml::Reader;
use std::{
    collections::HashMap,
    io::{Cursor, Read},
};
use zip::ZipArchive;

type Result<T> = std::result::Result<T, ParserError>;
type Id = String;
type Target = String;
type ImgNumber = u32;
type ImagesInfo = HashMap<(u32, ImgNumber), Vec<u8>>;

pub(crate) struct DocxParser {
    /// HashMap, где хранятся id картинок и текст извлеченный из них
    pub images: HashMap<Id, String>,
    pub img_info: ImagesInfo,
    temp_img_info: HashMap<Id, Vec<u8>>,
    cur_img_ind: ImgNumber,
}

impl DocxParser {
    /// Создает новый [`DocxParser`].
    pub(crate) fn new() -> Self {
        Self {
            images: HashMap::new(),
            img_info: HashMap::new(),
            temp_img_info: HashMap::new(),
            cur_img_ind: 0,
        }
    }

    /// Извлекает текстовые данные из параграфов, таблиц и из картинок из docx файлов
    ///
    /// # Arguments
    /// - `data` - слайс байтов данных из файла
    ///
    /// # Returns
    /// - Ok([`String`]) - возвращает текст
    /// - Err([`ParserError`]) - ошибка во время парсинга docx файла
    ///
    /// # Errors
    /// - [`ParserError::DocxError`] - ошибка во время docx
    /// - [`ParserError::ImageError`] - ошибка во время парсинга картинки
    /// - [`ParserError::ZipError`] - ошибка во время парсинга docx как zip
    /// - [`ParserError::XmlError`] - ошибка во время парсинга конфигурационного файла docx
    /// - Остальные [`ParserError`] связанные с Tesseract ошибки во время парсинга картинки
    pub(crate) fn get_from_docx(mut self, data: &[u8]) -> Result<(String, ImagesInfo)> {
        let dox = read_docx(data)?;
        // Вытаскиваем все картинки
        let images_bytes = self.extract_images_from_docx(data)?;
        // Парсим текст из картинок
        self.extract_text_from_images(images_bytes)?;

        Ok((
            dox.document
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
                .to_string(),
            self.img_info,
        ))
    }

    /// Проходится по всем парам
    ///
    /// # Arguments
    /// - `data` - слайс байтов данных docx файла
    ///
    /// # Returns
    /// - Ok([`HashMap<Id, Vec<u8>>`]) - возвращает имя словарь (id файла, байты файла)
    /// - Err([`ParserError`]) - ошибка во время парсинга картинки
    ///
    /// # Errors
    /// - [`ParserError::ImageError`] - ошибка во время парсинга картинки
    /// - Остальные [`ParserError`] связанные с Tesseract ошибки во время парсинга картинки
    fn extract_text_from_images(&mut self, images: HashMap<Id, Vec<u8>>) -> Result<()> {
        self.temp_img_info = images.clone();
        self.images = images
            .into_par_iter()
            .map(|(id, data)| Ok((id, get_from_image(&data)?)))
            .collect::<Result<HashMap<Id, String>>>()?;
        Ok(())
    }

    /// Извлекает все картинки из docx
    ///
    /// # Arguments
    /// - `data` - слайс байтов данных docx файла
    ///
    /// # Returns
    /// - Ok([`HashMap<Id, Vec<u8>>`]) - возвращает имя словарь (id файла, байты файла)
    /// - Err([`ParserError`]) - ошибка во время парсинга файла
    ///
    /// # Errors
    /// - [`ParserError::ZipError`] - ошибка во время парсинга docx как zip
    /// - [`ParserError::XmlError`] - ошибка во время парсинга конфигурационного файла docx
    fn extract_images_from_docx(&self, data: &[u8]) -> Result<HashMap<Id, Vec<u8>>> {
        let reader = Cursor::new(data);
        let mut archive = ZipArchive::new(reader)?;

        let images_info = Self::find_images_info(&mut archive)?;

        if images_info.is_empty() {
            return Ok(HashMap::new());
        }

        Self::extract_images(&mut archive, images_info)
    }

    /// Парсит конфигурационную xml из docx
    ///
    /// Проходит по всем файлам и ищет конфигурационную xml. При нахождении парсит
    /// из нее информацию о картинках.
    ///
    /// # Arguments
    /// - `archive` - docx открытый как [`ZipArchive`]
    ///
    /// # Returns
    /// - Ok([`HashMap<Target, Id>`]) - возвращает словарь (путь до файла, id файла)
    /// - Err([`ParserError`]) - ошибка во время парсинга файла
    ///
    /// # Errors
    /// - [`ParserError::ZipError`] - ошибка парсинга docx как zip
    /// - [`ParserError::XmlError`] - ошибка парсинга конфигурационного файла docx
    /// - [`ParserError::XmlAttrError`] - ошибка работы с аттрибутами в xml
    fn find_images_info(archive: &mut ZipArchive<Cursor<&[u8]>>) -> Result<HashMap<Target, Id>> {
        let mut rels_file = archive.by_name("word/_rels/document.xml.rels")?;
        let mut rels = Vec::new();
        rels_file.read_to_end(&mut rels)?;
        get_info_from_xml_rels(Reader::from_reader(rels.as_slice()))
    }

    /// Извлекает все картинки из docx ввиде словаря для дальнейшего парсинга
    ///
    /// # Arguments
    /// - `archive` - docx открытый как [`ZipArchive`]
    /// - `images_info` - словарь из пар пути до файла и id файла
    ///
    /// # Returns
    /// - Ok([`HashMap<Id, Vec<u8>>`]) - возвращает словарь (id файла, байты файла)
    /// - Err([`ParserError::ZipError`]) - ошибка во время парсинга файла
    fn extract_images(
        archive: &mut ZipArchive<Cursor<&[u8]>>,
        images_info: HashMap<Target, Id>,
    ) -> Result<HashMap<Id, Vec<u8>>> {
        let mut images_with_id = HashMap::new();

        for ind in 0..archive.len() {
            let mut file = archive.by_index(ind)?;
            let mut path = file.name();
            if path.starts_with("word/media/") {
                path = &path[5..];
            }

            if (path.starts_with("media/") || path.starts_with("image"))
                && let Some(id) = images_info.get(path.trim())
            {
                let mut buf = Vec::new();
                std::io::copy(&mut file, &mut buf)?;
                images_with_id.insert(id.clone(), buf);
            }
        }

        Ok(images_with_id)
    }

    // *************************************************************************
    // Работа с элементами docx
    // *************************************************************************

    /// Проходится по всем детям [`docx_rs::Paragraph`] и извлекает из них текст
    fn paragraph_unwrap(&mut self, paragraph: &docx_rs::Paragraph) -> String {
        paragraph
            .children
            .iter()
            .filter_map(|from| match from {
                docx_rs::ParagraphChild::Run(run) => Some(self.run_unwrap(run)),
                _ => None,
            })
            .collect::<String>()
    }

    /// Проходится по всем детям [`docx_rs::Run`] и извлекает из них текст
    fn run_unwrap(&mut self, run: &docx_rs::Run) -> String {
        run.children
            .iter()
            .filter_map(|from| match from {
                docx_rs::RunChild::Text(text) => Some(text.text.clone()),
                docx_rs::RunChild::Drawing(drawing) => self.drawing_unwrap(drawing).ok()?,
                _ => None,
            })
            .collect::<String>()
    }

    /// Извлекает текст из [`docx_rs::Drawing`], если он есть
    fn drawing_unwrap(&mut self, drawing: &docx_rs::Drawing) -> Result<Option<String>> {
        Ok(match &drawing.data {
            Some(docx_rs::DrawingData::Pic(pic)) => Some(self.pic_unwrap(pic)?),
            Some(docx_rs::DrawingData::TextBox(text_box)) => Some(self.text_box_unwrap(text_box)),
            _ => None,
        })
    }

    /// Подставляет текст с нужной картинки вместо [`docx_rs::Pic`]
    fn pic_unwrap(&mut self, pic: &docx_rs::Pic) -> Result<String> {
        match self.images.get(&pic.id) {
            Some(text) => {
                let data = self
                    .temp_img_info
                    .remove(&pic.id)
                    .expect("Байты картинки обязаны существовать в момент работы с картинкой");
                self.img_info.insert((0, self.cur_img_ind), data);
                Ok(text.clone())
            }
            None => Ok(String::new()),
        }
    }

    /// Извлекает текст из [`docx_rs::TextBox`]
    fn text_box_unwrap(&mut self, text_box: &docx_rs::TextBox) -> String {
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

    /// Проходится по всем детям [`docx_rs::Table`] и извлекает из них текст
    fn table_unwrap(&mut self, table: &docx_rs::Table) -> String {
        table
            .rows
            .iter()
            .map(|from| match from {
                docx_rs::TableChild::TableRow(table_row) => self.table_row_unwrap(table_row),
            })
            .collect::<String>()
    }

    /// Извлекает текст из [`docx_rs::TableRow`]
    fn table_row_unwrap(&mut self, table_row: &docx_rs::TableRow) -> String {
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

    /// Извлекает текст из [`docx_rs::TableCell`]
    fn table_cell_unwrap(&mut self, cell: &docx_rs::TableCell) -> String {
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
mod tests {
    use crate::{errors::ParserError, parsers::docx::DocxParser};
    use std::io::Cursor;
    use zip::ZipArchive;

    type Result<T> = std::result::Result<T, ParserError>;

    /// Считывает данные из файла ввиде byte vec
    fn read_data_from_file(file_name: &str) -> Result<Vec<u8>> {
        Ok(std::fs::read(file_name)?)
    }

    #[test]
    fn extract_xml_info() -> Result<()> {
        let data = read_data_from_file("assets/text_tables_png.docx")?;
        let reader = Cursor::new(&data[..]);
        let mut archive = ZipArchive::new(reader)?;

        let res = DocxParser::find_images_info(&mut archive)?
            .iter()
            .map(|(target, id)| format!("{target} : {id};\n"))
            .collect::<Vec<String>>()
            .join("\n");

        assert_eq!(
            res,
            String::from_utf8(read_data_from_file(
                "assets/tests_results/extract_xml_info.txt"
            )?)?
        );

        Ok(())
    }

    #[test]
    fn extract_media() -> Result<()> {
        let data = read_data_from_file("assets/text_tables_png.docx")?;
        let pars = DocxParser::new();
        let res = pars
            .extract_images_from_docx(&data)?
            .iter()
            .map(|(id, data_vec)| Ok(format!("{id} : {:?};\n", data_vec)))
            .collect::<Result<Vec<String>>>()?
            .join("\n");

        assert_eq!(
            res,
            String::from_utf8(read_data_from_file(
                "assets/tests_results/extract_media.txt"
            )?)?
        );

        Ok(())
    }

    fn extract_text_from_docx(extract_file: &str, check_file: &str) -> Result<()> {
        let data = read_data_from_file(extract_file)?;
        let pars = DocxParser::new();
        let (res, _) = pars.get_from_docx(&data)?;

        assert_eq!(
            res.trim(),
            String::from_utf8(read_data_from_file(check_file)?)?.trim()
        );
        Ok(())
    }

    #[test]
    fn extract_text_from_docx_without_png() -> Result<()> {
        extract_text_from_docx(
            "assets/text_and_tables.docx",
            "assets/tests_results/extract_text_from_docx_without_png.txt",
        )
    }

    #[test]
    fn extract_text_from_docx_with_png() -> Result<()> {
        extract_text_from_docx(
            "assets/text_tables_png.docx",
            "assets/tests_results/extract_text_from_docx_with_png.txt",
        )
    }
}
