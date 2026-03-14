//! Модуль для реализации парсеров

use std::collections::HashMap;

use crate::errors::ParserError;
pub(crate) mod docx;
pub(crate) mod image;
pub(crate) mod pdf;
pub(crate) mod pptx;
pub(crate) mod text;
pub(crate) mod xlsx;

mod xml;

type Result<T> = std::result::Result<T, ParserError>;
type ImgNum = u32;
type Bytes = u8;
type ImagesInfo = HashMap<(u32, ImgNum), Vec<Bytes>>;

/// Trait для парсеров MS office с извлечением текста и извлечением текста с изображений
pub(crate) trait MSOfficParser {
    fn get_text(self, data: &[Bytes]) -> Result<(String, ImagesInfo)>;
}
