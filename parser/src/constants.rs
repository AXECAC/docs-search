//! Константы используемые для парсера
//!
//! Содержит MIME константные типы для поддерживаемых форматов документов.

/// MIME тип для PDF документов
pub const APPLICATION_PDF: &str = "application/pdf";

/// MIME тип для DOCX документов
pub const APPLICATION_DOCX: &str =
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

/// MIME тип для DOCX документов
pub const APPLICATION_DOCX_ZIP: &str = "application/zip";

/// MIME тип для DOC документов
pub const APPLICATION_DOC: &str = "application/msword";

/// MIME тип для RTF документов
pub const APPLICATION_RTF: &str = "application/rtf";

/// MIME тип для XLSX (Microsoft Excel)
pub const APPLICATION_XLSX: &str =
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

/// MIME тип для XLS (Microsoft Excel)
pub const APPLICATION_XLS: &str = "application/vnd.ms-excel";

/// MIME тип для PPTX (Microsoft `PowerPoint`) презентаций
pub const APPLICATION_PPTX: &str =
    "application/vnd.openxmlformats-officedocument.presentationml.presentation";

/// MIME тип для PPT (Microsoft `PowerPoint`) презентаций
pub const APPLICATION_PPT: &str = "application/vnd.ms-powerpoint";
