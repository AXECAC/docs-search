from sqlalchemy import or_, cast, String

def is_empty_jsonb(col):
    return or_(
        col.is_(None),
        cast(col, String).in_(('null', '[]'))
    )
