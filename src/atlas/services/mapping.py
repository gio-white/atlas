from atlas.db.models import Entry
from atlas.domain import EntryView


def entry_view(entry: Entry) -> EntryView:
    return EntryView(
        occurred_on=entry.occurred_on,
        value_num=entry.value_num,
        value_bool=entry.value_bool,
        value_text=entry.value_text,
        occurred_at=entry.occurred_at,
        created_at=entry.created_at,
        id=entry.id,
    )
