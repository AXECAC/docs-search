//! Модуль для перевода старых форматов документов Microsoft office в новые
//!
//! Используется cli утилита поставляемая libreoffice - soffice

use crate::{
    constants::{APPLICATION_DOC, APPLICATION_PPT, APPLICATION_RTF, APPLICATION_XLS},
    errors::ParserError,
    match_parsers::{define_mime_type, read_data_from_file},
};

type Result<T> = std::result::Result<T, ParserError>;

pub(crate) fn convert_to_new_format(old_file_path: &str, new_path: &str) -> Result<()> {
    let file_data = read_data_from_file(old_file_path)?;
    match define_mime_type(&file_data) {
        Some(mime) if mime == APPLICATION_RTF || mime == APPLICATION_DOC => todo!(),
        Some(mime) if mime == APPLICATION_XLS => todo!(),
        Some(mime) if mime == APPLICATION_PPT => todo!(),
        Some(mime) => Err(ParserError::InvalidFormat(format!(
            "Не поддерживается данный тип файла {mime}"
        ))),
        None => Err(ParserError::InvalidFormat(
            "Не получается определить данный тип файла ".to_string(),
        )),
    }
}
