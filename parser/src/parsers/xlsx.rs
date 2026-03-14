//! Модуль для парсинга xlsx файлов.
//!
//! Для парсинга используется crate-ы calamine и zip

use std::{collections::HashMap, io::Cursor};

use calamine::{Reader, Xlsx};
use rayon::prelude::*;

use crate::{
    errors::ParserError,
    parsers::{MSOfficParser, image::get_from_image},
};

type Result<T> = std::result::Result<T, ParserError>;
type SheetIndex = u32;
type ImgOnSheetNum = u32;
type ImagesInfo = HashMap<(SheetIndex, ImgOnSheetNum), Vec<u8>>;

pub(crate) struct XlsxParser {
    /// HashMap для сопоставления байтов картинки с нужным sheet
    pub sheet_img_info: ImagesInfo,
    /// Текст sheet
    pub sheet_text: Vec<String>,
}
impl XlsxParser {
    /// Создает новый [`XlsxParser`].
    pub(crate) fn new() -> Self {
        Self {
            sheet_img_info: HashMap::new(),
            sheet_text: Vec::new(),
        }
    }
}
