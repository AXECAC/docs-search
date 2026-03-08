//! Модуль для перевода старых форматов документов Microsoft office в новые
//!
//! Используется cli утилита поставляемая libreoffice - soffice

use crate::{
    constants::{APPLICATION_DOC, APPLICATION_PPT, APPLICATION_RTF, APPLICATION_XLS},
    errors::ParserError,
    match_parsers::{define_mime_type, read_data_from_file},
};

type Result<T> = std::result::Result<T, ParserError>;

/// Перечисление старых форматов Microsoft office
enum MSOfficeFormat {
    /// doc like форматы
    Doc,
    /// xls like форматы
    Xls,
    /// ppt like форматы
    Ppt,
}

/// Конвертер старых Microsoft office форматов в новые
/// # Arguments
/// - `old_file_path` - путь по которому лежит файл старого формата
/// - `new_path` - путь по которому должен появить файл нового формата
///
/// # Errors
/// - [`ParserError::InvalidFormat`] - тип файла не поддерживается/не определен
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
