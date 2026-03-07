//! Парсинг pptx файлов
//!
//! Для парсинга используется crate rustypptx

use std::collections::HashMap;

use rayon::prelude::*;

use crate::{errors::ParserError, parsers::image::get_from_image};

type Result<T> = std::result::Result<T, ParserError>;
type SlideIndex = u32;
type ImgOnSlideNum = u32;
type ImagesInfo = HashMap<(SlideIndex, ImgOnSlideNum), Vec<u8>>;

pub(crate) struct PptxParser {
    /// HashMap для сопоставления байтов картинки с её местом в тексте слайда
    pub slides_img_info: ImagesInfo,
    /// Текст слайда (индекс слайда на 1 больше индекса в slides_text)
    pub slides_text: Vec<String>,
}

impl PptxParser {
    /// Создает новый [`PptxParser`].
    pub(crate) fn new() -> Self {
        Self {
            slides_img_info: HashMap::new(),
            slides_text: Vec::new(),
        }
    }

    /// Извлекает текстовые данные и текст из картинок
    ///
    /// # Arguments
    /// - `mut `[`self`] - сам парсер (забирает владение над парсером)
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

        result_text = self.add_text_from_img_in_slides()?;

        Ok((result_text, self.slides_img_info))
    }

    fn set_slides_text_and_img_info(&mut self, pptx_doc: rustypptx::PptxDocument) {
        for slide in pptx_doc.slides.iter() {
            for (ind, img) in slide.images.iter().enumerate() {
                self.slides_img_info
                    .insert((slide.index, ind as u32), img.data.clone());
            }

            self.slides_text.push(format!(
                "\n/*****************slide = {} ***************/\n {}\n",
                slide.index,
                slide
                    .text_elements
                    .iter()
                    .fold(String::new(), |mut sl_text, text_element| {
                        sl_text.push_str(&text_element.text);
                        sl_text.push('\n');
                        sl_text
                    })
            ));
        }
    }

    fn add_text_from_img_in_slides(&mut self) -> Result<String> {
        Ok(self
            .slides_text
            .par_iter()
            .enumerate()
            .map(|(sl_ind, text)| {
                let mut res_slide_text = String::from(text);

                for ((ind, img_num), data) in self
                    .slides_img_info
                    .iter()
                    .filter(|((ind, _), _)| *ind as usize == sl_ind + 1)
                {
                    res_slide_text.push_str(&format!(
                        "\n/********slide = {ind}; img_num = {img_num}********/\n"
                    ));

                    res_slide_text.push_str(&get_from_image(data)?);
                    res_slide_text
                        .push_str("\n/*****************************************************/");
                }
                Ok(res_slide_text)
            })
            .collect::<Result<Vec<_>>>()?
            .join("\n"))
    }
}
