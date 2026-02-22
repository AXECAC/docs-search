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
    #[error("IO error: {0}")]
    IoTempFileError(String),

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
