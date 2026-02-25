//! Типы для ошибок парсинга
//!
//! Содержит тип ParserError, который реализовывает конвертацию всех
//! потенциальных типов ошибок в себя для работы с единым стандартом ошибок в
//! парсере
use std::io;

use pyo3::exceptions::PyValueError;
use thiserror::Error;

/// Тип для ошибок парсинга
#[derive(Error, Debug)]
pub enum ParserError {
    /// Ошибка чтения файла
    ///
    /// Ошибки файловой системы, проблемы с правами доступа к файлам и т.д
    #[error("IO error: {0}")]
    IoError(#[from] io::Error),

    /// Ошибка создания временного файла
    #[error("Temp file error: {0}")]
    IoTempFileError(String),

    /// Ошибка парсинга utf-8 из байтов текстового файла
    #[error("From utf-8 error: {0}")]
    FromUTF8Error(#[from] std::string::FromUtf8Error),

    /// Ошибка чтения xml.rels
    ///
    /// Ошибки библиотеки для работы с xml
    #[error("Xml error: {0}")]
    XmlError(#[from] quick_xml::Error),

    /// Ошибка чтения docx/pptx/xlsx как zip
    ///
    /// Ошибки библиотеки для работы с zip
    #[error("Zip error: {0}")]
    ZipError(#[from] zip::result::ZipError),

    /// Ошибка работы с картинками
    ///
    /// Ошибки библиотеки image при конвертации слайса байтов в png
    #[error("Image error: {0}")]
    ImageError(#[from] image::ImageError),

    /// Ошибка чтения docx
    ///
    /// Ошибки библиотеки для работы с docx
    #[error("Docx error: {0}")]
    DocxError(#[from] docx_rs::ReaderError),

    /// Ошибка tesseract::InitializeError
    #[error("Tesseract init error: {0}")]
    TesseractInitError(#[from] tesseract::InitializeError),

    /// Ошибка tesseract::SetImageError
    #[error("Tesseract set image error: {0}")]
    TesseractSetImgError(#[from] tesseract::SetImageError),

    /// Ошибка tesseract::plumbing::TessBaseApiGetUtf8TextError
    #[error("Tesseract error: {0}")]
    TessBaseApiGetUtf8TextError(#[from] tesseract::plumbing::TessBaseApiGetUtf8TextError),

    /// Файл с данным расширением не поддерживается
    #[error("Invalid format error: {0}")]
    InvalidFormat(String),
}

impl From<ParserError> for pyo3::PyErr {
    fn from(value: ParserError) -> Self {
        PyValueError::new_err(value.to_string())
    }
}
