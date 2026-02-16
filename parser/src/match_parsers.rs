use std::{str::from_utf8, sync::LazyLock};

use infer::Infer;
use mime::{Mime, TEXT_PLAIN};

static INFER: LazyLock<Infer> = LazyLock::new(Infer::new);


/// Определяет MIME файла по считанным данным
pub fn define_mime_type(file_data: &[u8]) -> Option<Mime> {
    if let Some(kind) = INFER.get(file_data)
        && let Ok(mime) = kind.mime_type().parse()
    {
        return Some(mime);
    }

    if from_utf8(file_data).is_ok() {
        return Some(TEXT_PLAIN);
    }

    None
}
