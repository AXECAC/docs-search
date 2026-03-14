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

impl MSOfficParser for XlsxParser {
    /// Извлекает текстовые данные и текст из картинок
    ///
    /// # Arguments
    /// - `mut `[`self`] - сам парсер (забирает владение над парсером)
    /// - `data` - слайс байтов данных из файла
    ///
    /// # Returns
    /// - Ok([`String`]) - возвращает текст
    /// - Err([`ParserError`]) - ошибка во время парсинга xlsx файла
    ///
    /// # Errors
    /// - [`ParserError::XlsxError`] - ошибка во время парсинга xlsx
    /// - [`ParserError::ImageError`] - ошибка во время парсинга картинки
    /// - Остальные [`ParserError`] связанные с Tesseract ошибки во время парсинга картинки
    fn get_text(mut self, data: &[u8]) -> Result<(String, ImagesInfo)> {
        let cursor = Cursor::new(data);

        let mut excel = Xlsx::new(cursor)?;

        let sheet_names = excel.sheet_names().clone();

        for name in sheet_names {
            if let Ok(range) = excel.worksheet_range(&name) {
                let mut cur_sheet_text = String::new();
                cur_sheet_text.push_str("\n*** Sheet: ");
                cur_sheet_text.push_str(&name);
                cur_sheet_text.push_str(" ***\n");
                cur_sheet_text.push_str(
                    &range
                        .rows()
                        .map(|row| {
                            row.iter()
                                .map(std::string::ToString::to_string)
                                .collect::<Vec<String>>()
                                .join(",")
                        })
                        .collect::<Vec<String>>()
                        .join("\n"),
                );
                self.sheet_text.push(cur_sheet_text);
            }
        }

        Ok((self.sheet_text.join("\n"), self.sheet_img_info))
    }
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
