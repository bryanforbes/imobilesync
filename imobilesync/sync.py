from imobiledevice import idevice, Array, String
from imobilesync.plist_util import create_array

import datetime

__all__ = ['SyncError', 'SyncErrorCancel', 'Sync']

class SyncError(Exception):
    def __init__(self, value):
        self.value = value

    def get_array(self):
        pass

    def __str__(self):
        return repr(self.value)

class SyncErrorCancel(SyncError):
    def __init__(self, schema_type, reason):
        self.value = reason
        self.schema_type = schema_type

    def get_array(self):
        return create_array(
            "SDMessageCancelSession",
            self.schema_type,
            self.value
        )

class Sync(object):
    VERSION = 106
    SYNC_TYPES = [
        "SDSyncTypeFast",
        "SDSyncTypeSlow",
        "SDSyncTypeReset"
    ]

    def __get_device(self):
        return self.__device
    device = property(__get_device)

    def __get_uuid(self):
        return self.device.get_uuid()
    uuid = property(__get_uuid)

    def __init__(self, uuid=None):
        device = self.__device = idevice()

        if uuid is not None:
            if not device.init_device_by_uuid(uuid):
                raise SyncError('No iDevice with uuid %s.' % uuid)
        else:
            if not device.init_device():
                raise SyncError('No iDevice found.')

    def connect(self):
        lckd = self.device.get_lockdown_client()
        if not lckd:
            raise SyncError('Lockdown session couldn\'t be established.')

        msync = self.__mobile_sync = lckd.get_mobilesync_client()
        if not msync:
            raise SyncError('Mobilesync session couldn\'t be established.')

        del lckd

    def get_all_records(self, cls):
        obj = self.__get_records(cls)
        return obj.all()

    def get_changed_records(self, cls):
        obj = self.__get_records(cls)
        return obj.changes()

    def serialize_all(self, cls):
        objs = self.get_all_records(cls)
        return cls.serialize(self.uuid, objs)

    def serialize_changed(self, cls):
        objs = self.get_changed_records(cls)
        return cls.serialize(self.uuid, objs)

    def ping(self):
        msg = create_array(
            "DLMessagePing",
            "Preparing to get changes for device"
        )
        self.__mobile_sync.send(msg)

    def finish(self, cls, update_sync_time=False):
        self.__mobile_sync.send(
            cls.finish_message()
        )

        if update_sync_time:
            cls.state.last_sync_time = datetime.datetime.now()

        response = self.__mobile_sync.receive()
        if response[0].get_value() != "SDMessageDeviceFinishedSession" and \
            response[0].get_value() == "SDMessageCancelSession":
            raise SyncErrorCancel(cls.parent_schema_name, response[2].get_value())

    def disconnect(self):
        msg = create_array(
            "DLMessageDisconnect",
            "All done, thanks for the memories"
        )
        self.__mobile_sync.send(msg)

    def __get_records(self, cls):
        if cls.state.last_sync_time is not None:
            last_sync_time = cls.state.last_sync_time.strftime('%Y-%m-%d %H:%M:%S %z')
        else:
            last_sync_time = '---'
        self.__mobile_sync.send(
            cls.sync_message(
                last_sync_time,
                self.VERSION
            )
        )
        ret = self.__mobile_sync.receive()

        return cls(self.__mobile_sync)
