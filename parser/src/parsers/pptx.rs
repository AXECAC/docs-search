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

