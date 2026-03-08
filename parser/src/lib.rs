mod constants;
mod converter;
mod errors;
mod match_parsers;
mod parsers;

use pyo3::prelude::*;
use pyo3::{PyResult, types::PyModule};

/// Модуль для реализации функций модуля `docs_parser`
mod parser {
    use pyo3::prelude::*;

    /// Парсинг текста `from` файла по `path`
    #[pyo3::pyfunction]
    pub fn get_text(from_path: &str) -> PyResult<String> {
        Ok(crate::match_parsers::get_text(from_path)?)
    }

    /// Парсинг текста `from` файла по `path`
    #[pyo3::pyfunction]
    pub fn convert_to_new_format(old_file_path: &str, new_path: &str) -> PyResult<String> {
        // Ok(crate::match_parsers::get_text(from_path)?)
        todo!()
    }
}

/// Функция реализации python модуля, добавляющая в него функции
#[pymodule]
fn docs_parser(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parser::get_text, m)?)?;
    m.add_function(wrap_pyfunction!(parser::convert_to_new_format, m)?)?;
    Ok(())
}
