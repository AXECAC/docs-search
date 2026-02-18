//! Constants used throughout the parser library.
//!
//! Contains MIME type constants for various document formats supported.

/// MIME type for PDF documents
pub const APPLICATION_PDF: &str = "application/pdf";

/// MIME type for DOCX documents
pub const APPLICATION_DOCX: &str =
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

/// MIME type for DOCX documents
pub const APPLICATION_DOCX_ZIP: &str = "application/zip";

/// MIME type for XLSX (Microsoft Excel) spreadsheets
pub const APPLICATION_XLSX: &str =
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

/// MIME type for XLS (Microsoft Excel)
pub const APPLICATION_XLS: &str = "application/vnd.ms-excel";

/// MIME type for PPTX (Microsoft `PowerPoint`) presentations
pub const APPLICATION_PPTX: &str =
    "application/vnd.openxmlformats-officedocument.presentationml.presentation";
