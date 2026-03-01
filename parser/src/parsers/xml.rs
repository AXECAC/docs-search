//! Модуль парсеров конфигурационных файлов офиса для получения информации о
//! расположении картинок в docx/pptx/xlsx
//!
//! Для парсинга используется crate-ы quick_xml и zip

use crate::errors::ParserError;
use quick_xml::Reader;
use quick_xml::events::Event;
use std::collections::HashMap;

type Result<T> = std::result::Result<T, ParserError>;
type Target = String;
type Id = String;

/// Извлекает мета данные о картинках из конфигурационного файла docx в формате
/// словаря (target, id)
///
/// # Arguments
/// - `reader` - стрим на xml файл из docx
///
/// # Returns
/// - Ok([`HashMap<Target, Id>`]) - возвращает имя словарь (путь до файла, id файла)
/// - Err([`ParserError::XmlError`]) - ошибка во время парсинга конфигурационного файла docx
pub(crate) fn get_info_from_xml_rels<R: std::io::BufRead>(
    mut reader: Reader<R>,
) -> Result<HashMap<Target, Id>> {
    let mut buf = Vec::new();
    let mut images: HashMap<Target, Id> = HashMap::new();

    loop {
        match reader.read_event_into(&mut buf)? {
            Event::Empty(ref event) | Event::Start(ref event) => {
                if event.name().as_ref() == b"Relationship" {
                    let mut id = None;
                    let mut target = None;
                    let mut is_image = false;

                    for attr in event.attributes().with_checks(false) {
                        let attr = attr?;
                        match attr.key.as_ref() {
                            b"Id" => id = Some(attr.unescape_value()?),
                            b"Target" => target = Some(attr.unescape_value()?),
                            b"Type" => {
                                if attr.value.as_ref().ends_with(b"/image") {
                                    is_image = true;
                                }
                            }

                            _ => {}
                        }
                    }

                    if is_image && let (Some(id), Some(target)) = (id, target) {
                        images.insert(target.trim_start_matches('/').to_owned(), id.to_string());
                    }
                }
            }
            Event::Eof => break,
            _ => {}
        }

        buf.clear();
    }

    Ok(images)
}
