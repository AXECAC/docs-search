use std::io;

use thiserror::Error;

/// Тип для ошибок парсинга
#[derive(Error, Debug)]
pub enum ParserError {
    /// Ошибка чтения файла
    ///
    /// Ошибки файловой системы, проблемы с правами доступа к файлам и т.д
    #[error("IO error: {0}")]
    IoError(#[from] io::Error),

    /// Файл с данным расширением не поддерживается
    #[error("Invalid format error: {0}")]
    InvalidFormat(String),
}
