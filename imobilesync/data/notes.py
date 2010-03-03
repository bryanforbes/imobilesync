from imobilesync.data.base import BaseList, Base, RelatedBase
from imobilesync.config import state, config
from imobilesync.options import parser

__all__ = ['Note', 'Notes']

class Note(Base):
    entity_name = 'com.apple.notes.Note'

class Notes(BaseList):
    parent_schema_name = "com.apple.Notes"
    parent_schema_class = Note

    config = config.add('contacts', {})
    state = state.add('contacts', {
        'last_sync_time': None
    })

    def __init__(self, uuid, mobile_sync):
        super(Notes, self).__init__(uuid, mobile_sync)

parser.add_option('--notes', action='append_const', dest='sync_type', const=Notes)
