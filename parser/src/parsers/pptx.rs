//! Парсинг pptx файлов
//!
//! Для парсинга используется crate rustypptx

use std::collections::HashMap;

use crate::{errors::ParserError, parsers::image::get_from_image};

type Result<T> = std::result::Result<T, ParserError>;
type SlideIndex = u32;
type ImgOnSlideNum = u32;
type ImagesInfo = HashMap<(SlideIndex, ImgOnSlideNum), Vec<u8>>;

pub(crate) struct PptxParser {
    /// HashMap для сопоставления байтов картинки с её местом в тексте слайда
    pub slides_img_info: ImagesInfo,
    /// HashMap из индекса слайда и текста извлеченного из него
    pub slides_text: HashMap<SlideIndex, String>,
}

impl PptxParser {
    /// Создает новый [`PptxParser`].
    pub(crate) fn new() -> Self {
        Self {
            slides_img_info: HashMap::new(),
            slides_text: HashMap::new(),
        }
    }

    /// Извлекает текстовые данные и текст из картинок
    ///
    /// # Arguments
    /// - `data` - слайс байтов данных из файла
    ///
    /// # Returns
    /// - Ok([`String`]) - возвращает текст
    /// - Err([`ParserError`]) - ошибка во время парсинга pptx файла
    ///
    /// # Errors
    /// - [`ParserError::PptxError`] - ошибка во время парсинга pptx
    /// - [`ParserError::ImageError`] - ошибка во время парсинга картинки
    /// - Остальные [`ParserError`] связанные с Tesseract ошибки во время парсинга картинки
    pub(crate) fn get_from_pptx(mut self, data: &[u8]) -> Result<(String, ImagesInfo)> {
        let pptx_doc = rustypptx::parse_pptx_bytes(data)?;

        let mut result_text = String::new();
        if let Some(title) = &pptx_doc.metadata.title {
            result_text.push_str(&format!("Название: {title}"));
        }

        self.set_slides_text_and_img_info(pptx_doc);

        result_text = self
            .slides_text
            .iter_mut()
            .map(|(sl_ind, text)| {
                text.push_str(
                    &self
                        .slides_img_info
                        .iter()
                        .filter(|((ind, _), _)| *ind == *sl_ind)
                        .map(|((_, img_num), data)| {
                            Ok(format!(
                                "\n/********slide = {sl_ind}; img_num = {img_num}********/\n \
                                {}\n \
                                /****************************/",
                                get_from_image(data)?
                            ))
                        })
                        .collect::<Result<Vec<_>>>()?
                        .join("\n"),
                );
                Ok(text.clone())
            })
            .collect::<Result<Vec<_>>>()?
            .join("\n");

        Ok((result_text, self.slides_img_info))
    }

    fn set_slides_text_and_img_info(&mut self, pptx_doc: rustypptx::PptxDocument) {
        for slide in pptx_doc.slides.iter() {
            self.slides_img_info =
                slide
                    .images
                    .iter()
                    .enumerate()
                    .fold(HashMap::new(), |mut info, (ind, img)| {
                        info.insert((slide.index, ind as u32), img.data.clone());
                        info
                    });
            self.slides_text =
                slide
                    .text_elements
                    .iter()
                    .fold(HashMap::new(), |mut sl_text, text_element| {
                        sl_text.insert(slide.index, text_element.text.clone());
                        sl_text
                    })
        }
    }
}
