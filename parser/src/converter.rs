//! Модуль для перевода старых форматов документов Microsoft office в новые
//!
//! Используется cli утилита поставляемая libreoffice - soffice

use std::process::{Command, Stdio};

use crate::{
    constants::{APPLICATION_DOC, APPLICATION_PPT, APPLICATION_RTF, APPLICATION_XLS},
    errors::ParserError,
    match_parsers::{define_mime_type, read_data_from_file},
};

type Result<T> = std::result::Result<T, ParserError>;

/// Поддерживаемые типы старых форматов Microsoft office
enum MSOfficeFormat {
    /// doc like форматы
    Doc,
    /// xls like форматы
    Xls,
    /// ppt like форматы
    Ppt,
}

/// Конвертер старых Microsoft office форматов в новые
///
/// Определяет формат и вызывает конвертацию файла
/// # Arguments
/// - `old_file_path` - путь по которому лежит файл старого формата
/// - `new_path` - путь по которому должен появить файл нового формата
///
/// # Errors
/// - [`ParserError::InvalidFormat`] - тип файла не поддерживается/не определен
/// - [`ParserError::IoError`] - проблемы с libreoffice
pub(crate) fn convert_to_new_format(old_file_path: &str, new_path: &str) -> Result<()> {
    let file_data = read_data_from_file(old_file_path)?;
    match define_mime_type(&file_data) {
        Some(mime) if mime == APPLICATION_RTF || mime == APPLICATION_DOC => {
            converter_files(MSOfficeFormat::Doc, old_file_path, new_path)
        }
        Some(mime) if mime == APPLICATION_XLS => {
            converter_files(MSOfficeFormat::Xls, old_file_path, new_path)
        }
        Some(mime) if mime == APPLICATION_PPT => {
            converter_files(MSOfficeFormat::Ppt, old_file_path, new_path)
        }
        Some(mime) => Err(ParserError::InvalidFormat(format!(
            "Не поддерживается данный тип файла {mime}"
        ))),
        None => Err(ParserError::InvalidFormat(
            "Не получается определить данный тип файла ".to_string(),
        )),
    }
}

/// Конвертирует файл в новый формат в зависимости от типа
/// # Arguments
/// - `old_file_path` - путь по которому лежит файл старого формата
/// - `new_path` - путь по которому должен появить файл нового формата
///
/// # Errors
/// - [`ParserError::IoError`] - проблемы с libreoffice
fn converter_files(type_format: MSOfficeFormat, old_file_path: &str, new_path: &str) -> Result<()> {
    let type_convert = match type_format {
        MSOfficeFormat::Doc => "docx",
        MSOfficeFormat::Xls => "xlsx",
        MSOfficeFormat::Ppt => "pptx",
    };

    Command::new("soffice")
        .arg("--headless")
        .arg("--convert-to")
        .arg(type_convert)
        .arg(old_file_path)
        .arg("--outdir")
        .arg(new_path)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()?;
    Ok(())
}
