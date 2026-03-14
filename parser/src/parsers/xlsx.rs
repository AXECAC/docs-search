//! Модуль для парсинга xlsx файлов.
//!
//! Для парсинга используется crate-ы calamine и zip

use std::{collections::HashMap, fmt::Write, io::Cursor};

use calamine::{Reader, Xlsx};
use rayon::prelude::*;
use zip::ZipArchive;

use crate::{
    errors::ParserError,
    parsers::{MSOfficeParser, image::extract_text_from_image},
};

type Bytes = u8;
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

impl MSOfficeParser for XlsxParser {
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
    /// - [`ParserError::FmtError`] - ошибка во время записи в буффер
    /// - [`ParserError::ZipError`] - ошибка во время парсинга docx как zip
    /// - Остальные [`ParserError`] связанные с Tesseract ошибки во время парсинга картинки
    fn extract_text(mut self, data: &[Bytes]) -> Result<(String, ImagesInfo)> {
        let cursor = Cursor::new(data);

        let excel = Xlsx::new(cursor)?;
        let sheet_names = excel.sheet_names();

        // чтение текста с страниц
        self.read_sheets(excel, sheet_names)?;

        // Вытаскиваем все картинки и парсим из них текст
        let text_from_images = self.extract_images_from_xlsx(data)?;

        Ok((
            format!(
                "{}\n{}",
                self.sheet_text.join("\n").trim(),
                text_from_images
            ),
            self.sheet_img_info,
        ))
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

    ///  Читает текст со всех страниц
    ///
    /// # Arguments
    /// - `excel` - документ
    /// - `sheet_names` - названия страниц
    ///
    /// # Errors
    /// - [`ParserError::XlsxError`] - ошибка во время парсинга xlsx
    /// - [`ParserError::FmtError`] - ошибка во время записи в буффер
    /// - Остальные [`ParserError`] связанные с Tesseract ошибки во время парсинга картинки
    fn read_sheets(
        &mut self,
        mut excel: Xlsx<Cursor<&[u8]>>,
        sheet_names: Vec<String>,
    ) -> Result<()> {
        for name in sheet_names {
            if let Ok(range) = excel.worksheet_range(&name) {
                let mut cur_sheet_text = String::new();
                cur_sheet_text.push_str("/*** Sheet: ");
                cur_sheet_text.push_str(&name);
                cur_sheet_text.push_str(" ***/\n");

                // чтение текста из ячеек
                range.rows().try_for_each(|row| -> Result<()> {
                    row.iter().enumerate().try_for_each(|(index, cell)| {
                        if index > 0 {
                            cur_sheet_text.push_str(", ");
                        }
                        write!(cur_sheet_text, "{cell}")
                    })?;
                    cur_sheet_text.push('\n');
                    Ok(())
                })?;

                self.sheet_text.push(cur_sheet_text);
            }
        }
        Ok(())
    }

    /// Извлекает все картинки из xlsx и парсит их
    ///
    /// # Arguments
    /// - `data` - слайс байтов данных xlsx файла
    ///
    /// # Returns
    /// - Ok([`String`]) - возвращает текст со всех картинок
    /// - Err([`ParserError`]) - ошибка во время парсинга xlsx файла
    ///
    /// # Errors
    /// - [`ParserError::ZipError`] - ошибка во время парсинга xlsx как zip
    /// - [`ParserError::ImageError`] - ошибка во время парсинга картинки
    fn extract_images_from_xlsx(&mut self, data: &[Bytes]) -> Result<String> {
        let reader = Cursor::new(data);
        let mut archive = ZipArchive::new(reader)?;

        // Находим все картинки
        let mut images_data: Vec<Vec<Bytes>> = Vec::new();
        for ind in 0..archive.len() {
            let mut file = archive.by_index(ind)?;
            let path = file.name();

            if path.starts_with("xl/media/") {
                let mut buf = Vec::new();
                std::io::copy(&mut file, &mut buf)?;
                images_data.push(buf);
            }
        }

        // Извлекам текст из картинок
        let extracted_data = images_data
            .par_iter()
            .enumerate()
            .map(|(img_num, img_data)| {
                let text = extract_text_from_image(img_data)?;
                Ok((img_num, img_data, text))
            })
            .collect::<Result<Vec<_>>>()?;

        // Сохраняем данные о картинке и тексте
        let mut text_from_images = String::new();
        for (img_num, img_data, text) in extracted_data {
            text_from_images.push_str("\n/************* Image = ");
            text_from_images.push_str(&img_num.to_string());
            text_from_images.push_str(" *************/\n");
            text_from_images.push_str(&text);
            text_from_images.push_str("\n/*************************************/\n");
            self.sheet_img_info
                .insert((0, img_num as u32), img_data.to_owned());
        }

        Ok(text_from_images)
    }
}
