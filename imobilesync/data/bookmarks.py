from imobilesync.data.base import BaseList, Base, RelatedBase
from imobilesync.config import config, state
from imobilesync.options import parser

__all__ = ['Bookmark', 'Bookmarks']

TYPE_FIREFOX = 0
TYPE_CHROME = 1
TYPE_CHROMIUM = 2

class Bookmark(Base):
    entity_name = 'com.apple.bookmarks.Bookmark'

class Bookmarks(BaseList):
    parent_schema_name = "com.apple.Bookmarks"
    parent_schema_class = Bookmark

    config = config.add('bookmarks', {})
    state = state.add('bookmarks', {
        'last_sync_time': None
    })

    def __init__(self, uuid, mobile_sync):
        super(Bookmarks, self).__init__(uuid, mobile_sync)

parser.add_option('--bookmarks', action='append_const', dest='sync_type', const=Bookmarks)
