use pyo3::prelude::*;
use pyo3::{PyResult, types::PyModule};

pub fn add(left: u64, right: u64) -> u64 {
    left + right
}

mod parser {
    use pyo3::prelude::*;
    #[pyo3::pyfunction]
    pub fn add(left: u64, right: u64) -> PyResult<u64> {
        Ok(crate::add(left, right))
    }
}

#[pymodule]
fn docs_parser(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parser::add, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use crate::add;

    #[test]
    fn it_works() {
        let result = add(2, 2);
        assert_eq!(result, 4);
    }
}
