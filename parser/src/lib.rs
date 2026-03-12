mod constants;
mod converter;
mod errors;
mod match_parsers;
mod parsers;

use pyo3::prelude::*;
use pyo3::{PyResult, types::PyModule};

/// Модуль для реализации функций модуля `docs_parser`
mod parser {
    use std::collections::HashMap;

    use pyo3::prelude::*;
    type ImgNumber = u32;
    type ImagesInfo = HashMap<(u32, ImgNumber), Vec<u8>>;

    /// Парсинг текста `from` файла по `path`
    #[pyo3::pyfunction]
    pub fn get_text(from_path: &str) -> PyResult<(String, ImagesInfo)> {
        Ok(crate::match_parsers::get_text(from_path)?)
    }

    /// Конвертер старых Microsoft office форматов в новые
    #[pyo3::pyfunction]
    pub fn convert_to_new_format(old_file_path: &str, new_path: &str) -> PyResult<()> {
        Ok(crate::converter::convert_to_new_format(
            old_file_path,
            new_path,
        )?)
    }
}

/// Функция реализации python модуля, добавляющая в него функции
#[pymodule]
fn docs_parser(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parser::get_text, m)?)?;
    m.add_function(wrap_pyfunction!(parser::convert_to_new_format, m)?)?;
    Ok(())
}
