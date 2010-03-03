# -*- coding: utf-8 -*-
import logging
log = logging.getLogger("modules.iDevice")

import conduit
import conduit.dataproviders.HalFactory as HalFactory
import conduit.dataproviders.DataProvider as DataProvider
import conduit.dataproviders.DataProviderCategory as DataProviderCategory
import conduit.datatypes.DataType as DataType
import conduit.TypeConverter as TypeConverter
import conduit.utils as Utils
import conduit.Exceptions as Exceptions

import conduit.datatypes.Contact as Contact
import conduit.datatypes.Event as Event
import conduit.datatypes.Event as Bookmark

Utils.dataprovider_add_dir_to_path(__file__)

from imobilesync.sync import SyncFactory, SyncError
from imobilesync.data import Calendars, Contacts

MODULES = {
    "iDeviceFactory": { "type": "dataprovider-factory" },
    "iDeviceConverter": { "type": "converter" }
}

class iDeviceFactory(HalFactory.HalFactory):
    """
    Detects when an iPhone is mounted and creates the appropriate dataproviders
    """
    __vendor_id = 0x05ac
    __supported_devices = [
        0x1290, # iPhone
        0x1291, # iPod Touch
        0x1292, # iPhone 3G
        0x1293, # iPod Touch 2G
        0x1294, # iPhone 3GS
        0x1295, # Unknown
        0x1296, # Unknown
        0x1297, # Unknown
        0x1298, # Unknown
        0x1299  # iPod Touch 3G 64GB
    ]
    # Defined by fd icon spec and gratefully supplied by dobey
    __model_icons = {
            "iPhone": "phone-apple-iphone",
            "iPhone 3G": "phone-apple-iphone",
            "iPod": "multimedia-player-apple-ipod-touch"
    }
    def is_interesting(self, udi, props):
        # Check for vendor and product id
        if props.get("usb_device.vendor_id") == self.__vendor_id:
            if props.get("usb_device.product_id") in self.__supported_devices:
                return True
        return False

    def get_category(self, udi, **props):
        product = props.get("usb_device.product")
        icon = self.__model_icons[product]
        return DataProviderCategory.DataProviderCategory(
                    product,
                    icon,
                    udi)

    def get_dataproviders(self, udi, **kwargs):
        # FIXME: Query lockdownd for supported data classes
        return [iDeviceContactsTwoWay, iDeviceCalendarsTwoWay]

    def get_args(self, udi, **props):
        product = props.get("usb_device.product")
        props["uuid"] = props.get("usb_device.serial")
        props["model"] = product
        return (props["uuid"], props["model"], udi)

class iDeviceDataProviderTwoWay(DataProvider.TwoWay):
    _category_ = conduit.dataproviders.CATEGORY_MISC
    _module_type_ = 'twoway'

    def __init__(self, *args):
        self.uuid = str(args[0])
        self.model = str(args[1])
        self.hal_udi = str(args[2])

        try:
            self.sync = SyncFactory.get(self.uuid)
        except SyncError, e:
            log.info("Failed to connect to iPhone/iPod Touch")
        else:
            log.info("Connected to %s with uuid %s" % (self.model, self.uuid))

        DataProvider.TwoWay.__init__(self)

    def uninitialize(self):
        pass
        #self.sync.disconnect()

    def refresh(self):
        DataProvider.TwoWay.refresh(self)
        self._refresh()

    def _refresh(self):
        self.data = self.sync.get_all_records_hashed(self.data_class)
        self.sync.finish(self.data_class, True)

    def get(self, LUID):
        DataProvider.TwoWay.get(self, LUID)
        data = self._get_data(LUID)
        data.set_UID(LUID)
        return data

    def get_all(self):
        DataProvider.TwoWay.get_all(self)
        return [record.uuid for record in self.data.values()]

class iDeviceContactsTwoWay(iDeviceDataProviderTwoWay):
    """
    Contact syncing for iPhone and iPod Touch
    """

    _name_ = "iPhone Contacts"
    _description_ = "iPhone and iPod Touch Contact Dataprovider"
    _in_type_ = "idevice/contact"
    _out_type_ = "idevice/contact"
    _icon_ = "contact-new"

    data_class = Contacts

    def get_UID(self):
        return "iDeviceContactsTwoWay-%s" % self.uuid

    def _get_data(self, LUID):
        return iDeviceContact(uri=LUID, record=self.data[LUID])

class iDeviceCalendarsTwoWay(iDeviceDataProviderTwoWay):
    """
    Contact syncing for iPhone and iPod Touch
    """

    _name_ = "iPhone Calendar"
    _description_ = "iPhone and iPod Touch Calendar Dataprovider"
    _in_type_ = "idevice/event"
    _out_type_ = "idevice/event"
    _icon_ = "appointment-new"
    _configurable_ = True

    data_class = Calendars

    def __init__(self, *args):
        iDeviceDataProviderTwoWay.__init__(self, *args)

        self.update_configuration(
            _calendarId=""
        )
    def get_UID(self):
        return "iDeviceCalendarsTwoWay-%s" % self.uuid

    def _get_data(self, LUID):
        return iDeviceCalendar(uri=LUID, record=self.data[LUID])

    def config_setup(self, config):
        config.add_section("Calendar Name")
        config.add_item("Calendar", "combo", config_name = "_calendarId", choices = self._calendar_names())

class iDeviceConverter(TypeConverter.Converter):
    def __init__(self):
        self.conversions = {
            "idevice/contact,contact": self.idevice_contact_to_contact,
            "idevice/event,event": self.idevice_event_to_event
        }

    def idevice_contact_to_contact(self, data, **kwargs):
        c = Contact.Contact(vcard=data.get_vcard())
        return c

    def idevice_event_to_event(self, data, **kwargs):
        e = Event.Event()
        e.iCal = data.get_ical()
        return e

class iDeviceDataType(DataType.DataType):
    def __init__(self, uri, **kwargs):
        DataType.DataType.__init__(self)
        self.record = kwargs.get("record", None)
    def __str__(self):
        return self.get_string()

    def get_hash(self):
        return hash(self.record)

class iDeviceContact(iDeviceDataType):
    _name_ = 'idevice/contact'

    def get_vcard(self):
        return self.record.__vcard__()

    def get_string(self):
        return 'iDeviceContact: %s' % str(self.record)

class iDeviceEvent(iDeviceDataType):
    _name_ = 'idevice/event'

    def get_ical(self):
        return self.record.__ical__()

    def get_string(self):
        return 'iDeviceCalendar: %s' % str(self.record)
