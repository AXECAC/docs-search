mod constants;
mod errors;
mod match_parsers;
mod parsers;

use pyo3::prelude::*;
use pyo3::{PyResult, types::PyModule};

mod parser {
    use pyo3::prelude::*;

    /// Parsing text `from` file by `path`
    #[pyo3::pyfunction]
    pub fn get_text(from_path: &str) -> PyResult<String> {
        Ok(crate::match_parsers::get_text(from_path)?)
    }
}

#[pymodule]
fn docs_parser(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parser::get_text, m)?)?;
    Ok(())
}
