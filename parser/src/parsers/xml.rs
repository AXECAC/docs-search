//! Модуль парсеров конфигурационных файлов офиса для получения информации о
//! расположении картинок в docx/pptx/xlsx
//!
//! Для парсинга используется crate-ы quick_xml и zip

use crate::errors::ParserError;
use quick_xml::Reader;
use quick_xml::events::Event;
use std::collections::HashMap;
use std::io::{BufReader, Cursor};
use zip::read::ZipFile;

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
/// - `Ok(HashMap<Target, Id>)` - возвращает имя словарь (путь до файла, id файла)
/// - `Err(`[`ParserError::XmlError`]`)` - ошибка во время парсинга конфигурационного файла docx
pub(crate) fn get_info_from_xml_rels(
    mut reader: Reader<BufReader<ZipFile<'_, Cursor<&[u8]>>>>,
) -> Result<HashMap<Target, Id>> {
    let mut buf = Vec::new();
    let mut images: HashMap<Target, Id> = HashMap::new();

    loop {
        match reader.read_event_into(&mut buf) {
            Ok(Event::Empty(ref event)) | Ok(Event::Start(ref event)) => {
                if event.name().as_ref() == b"Relationship" {
                    let mut id = None;
                    let mut target = None;
                    let mut rel_type = None;

                    for attr in event.attributes().with_checks(false).flatten() {
                        match attr.key.as_ref() {
                            b"Id" => id = Some(attr.unescape_value()?.to_string()),
                            b"Target" => target = Some(attr.unescape_value()?.to_string()),
                            b"Type" => rel_type = Some(attr.unescape_value()?.to_string()),
                            _ => {}
                        }
                    }

                    if let (Some(id), Some(mut target), Some(rel_type)) = (id, target, rel_type)
                        && rel_type.ends_with("/image")
                    {
                        if target.starts_with('/') {
                            target = target[1..].to_string()
                        }
                        images.insert(target, id);
                    }
                }
            }
            Ok(Event::Eof) => break,
            Err(e) => return Err(ParserError::XmlError(e)),
            _ => {}
        }

        buf.clear();
    }

    Ok(images)
}
