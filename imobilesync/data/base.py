from imobilesync.plist_util import create_array, EMPTY_PARAM
from imobilesync.sync import SyncErrorCancel
from imobilesync.config import state

from plist import PLIST_STRING, PLIST_DICT, PLIST_ARRAY, PLIST_NONE, PLIST_DATA, PLIST_DATE, PLIST_UINT
from datetime import timedelta
import time

import pdb

__all__ = ["Base", "BaseList"]

RECORD_ENTITY_NAME_KEY = "com.apple.syncservices.RecordEntityName"
ODD_EPOCH = timedelta(seconds=978307200) # For some reason Apple decided the epoch was on a different day?

class Base(object):
    entity_name = ''

    related_classes = ()

    def __init__(self, uuid, record_id, record_dict):
        self._uuid = uuid
        self.__record_id = record_id
        self.__record_dict = record_dict

        self.__data = {}

        for cls in self.related_classes:
            setattr(self, cls.parent_prop, {})

        for key in record_dict:
            value = record_dict[key]
            key_us = key.replace(' ', '_')
            if value.get_type() == PLIST_ARRAY:
                self.__data[key_us] = [value[i].get_value() for i in range(len(value))]
            elif value.get_type() == PLIST_NONE:
                self.__data[key_us] = None
            elif value.get_type() == PLIST_DATA:
                self.__data[key_us] = str(value.get_value())
            elif value.get_type() == PLIST_DATE:
                self.__data[key_us] = value.get_value() + ODD_EPOCH
            elif value.get_type() == PLIST_UINT:
                self.__data[key_us] = value.get_value()
            else:
                self.__data[key_us] = str(value.get_value()).replace('\n', '\\n')

    def __getattr__(self, name):
        if self.__data.has_key(name):
            return self.__data[name]
        else:
            raise AttributeError(name)

    def __get_record_id(self):
        return self.__record_id
    id = property(__get_record_id)

    def __get_unique_id(self):
        return '%s@iphone-%s' % (self.__record_id, self._uuid)
    uuid = property(__get_unique_id)

    def __get_record_dict(self):
        return self.__record_dict
    record_dict = property(__get_record_dict)

class RelatedBase(Base):
    parent_key = ''
    parent_prop = ''

    def __get_parent_id(self):
        return self.record_dict[self.parent_key][0].get_value()
    parent_id = property(__get_parent_id)

    def get_type_or_label(self):
        if self.type == 'other' and hasattr(self, 'label'):
            return self.label
        else:
            return self.type

class BaseList(object):
    parent_schema_name = ''
    parent_schema_class = Base

    related_schema_classes = ()

    config = None
    state = None

    def __init__(self, uuid, mobile_sync):
        self._uuid = uuid
        self._mobile_sync = mobile_sync
        self._parent_records = {}

        self.__related_class_map = {}
        for cls in self.parent_schema_class.related_classes:
            self.__related_class_map[cls.entity_name] = cls

    @classmethod
    def sync_message(cls, last_sync_time, version):
        return create_array(
            "SDMessageSyncDataClassWithDevice",
            cls.parent_schema_name,
            last_sync_time,
            time.strftime('%Y-%m-%d %H-%M-%S %z'),
            version,
            None # Empty parameter
        )

    @classmethod
    def finish_message(cls):
        return create_array(
            "SDMessageFinishSessionOnDevice",
            cls.parent_schema_name
        )

    @staticmethod
    def serialize(records):
        output = [record.serialize() for record in records]
        return ''.join(output)

    def all(self):
        msg = create_array(
            'SDMessageGetAllRecordsFromDevice',
            self.parent_schema_name
        )

        return self.__receive_records(msg)

    def changes(self):
        msg = create_array(
            'SDMessageGetChangesFromDevice',
            self.parent_schema_name
        )
        return self.__receive_records(msg)

    def __receive_records(self, record_type):
        self._mobile_sync.send(record_type)

        record = self._mobile_sync.receive()

        while record[0].get_value() != 'SDMessageDeviceReadyToReceiveChanges':
            # check message type and schema name
            if record[0].get_value() != 'SDMessageProcessChanges' or \
                record[1].get_value() != self.parent_schema_name:
                raise SyncErrorCancel(self.parent_schema_name, "Could not commit changes from device.")

            # make sure we got a dict node next
            if record[2].get_type() == PLIST_STRING and record[2].get_value() == EMPTY_PARAM:
                # skip this record set since we got no change data
                pass
            elif record[2].get_type() != PLIST_DICT:
                raise SyncErrorCancel(self.parent_schema_name, "Could not commit changes from device.")
            else:
                records = record[2]
                for record_id, record_dict in records.items():
                    record_entity_name = record_dict[RECORD_ENTITY_NAME_KEY].get_value()

                    self._process_record(record_entity_name, record_id, record_dict)

            msg = create_array(
                'SDMessageAcknowledgeChangesFromDevice',
                self.parent_schema_name
            )
            self._mobile_sync.send(msg)
            record = self._mobile_sync.receive()

        for obj in self._parent_records.values():
            yield obj

    def _process_record(self, entity_name, id, record):
        if entity_name == self.parent_schema_class.entity_name:
            self._parent_records[id] = self.parent_schema_class(self._uuid, id, record)
        elif entity_name in self.__related_class_map:
            cls = self.__related_class_map[entity_name]
            obj = cls(self._uuid, id, record)

            self._process_related_record(obj)

    def _process_related_record(self, related_record):
        parent_objs = getattr(self._parent_records[related_record.parent_id], related_record.parent_prop)
        parent_objs[related_record.id] = related_record
