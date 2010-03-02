from imobilesync.data.base import BaseList, Base, RelatedBase
from imobilesync.config import state
import vobject, time, base64

__all__ = ['Contact', 'Contacts']

class ContactRelated(RelatedBase):
    entity_name = 'com.apple.contacts.Contact'
    parent_key = 'contact'

    def __str__(self):
        if hasattr(self, 'label'):
            return '%s: %s' % (self.label, self.value)
        else:
            return '%s: %s' % (self.type, self.value)
    __repr__ = __str__

class CalendarURI(ContactRelated):
    entity_name = 'com.apple.contacts.CalendarURI'
    parent_prop = 'calendar_uris'

class CustomField(ContactRelated):
    entity_name = 'com.apple.contacts.Custom Field'
    parent_prop = 'custom_fields'

class Date(ContactRelated):
    entity_name = 'com.apple.contacts.Date'
    parent_prop = 'dates'

    def serialize(self, card):
        t = self.get_type_or_label()
        # TODO: more types
        if t == "anniversary":
            anniv = card.add('x-evolution-anniversary')
            anniv.value = self.value.strftime("%Y-%m-%d")

class EmailAddress(ContactRelated):
    entity_name = 'com.apple.contacts.Email Address'
    parent_prop = 'email_addresses'

    def serialize(self, card):
        email = card.add('email')
        email.params['TYPE'] = [self.get_type_or_label().upper()]
        email.value = self.value

class Group(ContactRelated):
    entity_name = 'com.apple.contacts.Group'
    parent_prop = 'groups'

    def __get_parent_ids(self):
        return [id.get_value() for id in self.record_dict[self.parent_key]]
    parent_ids = property(__get_parent_ids)

class IM(ContactRelated):
    entity_name = 'com.apple.contacts.IM'
    parent_prop = 'ims'

    def serialize(self, card):
        im = card.add('x-%s' % self.service)
        im.value = self.user
        im.params['TYPE'] = [self.get_type_or_label().upper()]

class PhoneNumber(ContactRelated):
    entity_name = 'com.apple.contacts.Phone Number'
    parent_prop = 'phone_numbers'

    def serialize(self, card):
        tel = card.add('tel')
        teltype = self.get_type_or_label().upper()
        # MobileSync sends "mobile" for phones, which according to RFCs is wrong
        if teltype == "MOBILE":
            teltype = "CELL"
        tel.value = self.value
        tel.params['TYPE'] = [teltype]

class RelatedName(ContactRelated):
    entity_name = 'com.apple.contacts.Related Name'
    parent_prop = 'related_names'

class StreetAddress(ContactRelated):
    entity_name = 'com.apple.contacts.Street Address'
    parent_prop = 'street_addresses'

    def __get_address_dict(self):
        def get_value(name):
            return self.record_dict[name].get_value()
        address = {}
        if self.record_dict.has_key('street'):
            address['street'] = get_value('street')
        if self.record_dict.has_key('street'):
            address['city'] = get_value('city')
        if self.record_dict.has_key('country code'):
            address['region'] = get_value('country code')
        if self.record_dict.has_key('postal code'):
            address['code'] = get_value('postal code')
        if self.record_dict.has_key('country'):
            address['country'] = get_value('country')

        return address
    address_dict = property(__get_address_dict)

    def serialize(self, card):
        adr = card.add('adr')
        adr.value = vobject.vcard.Address(**self.address_dict)
        adr.params['TYPE'] = [self.get_type_or_label().upper()]

class URL(ContactRelated):
    entity_name = 'com.apple.contacts.URL'
    parent_prop = 'urls'

    def serialize(self, card):
        url = card.add('url')
        url.value = self.value
        url.params['TYPE'] = [self.get_type_or_label().upper()]

class Contact(Base):
    entity_name = 'com.apple.contacts.Contact'

    related_classes = (
        CalendarURI,
        CustomField,
        Date,
        EmailAddress,
        Group,
        IM,
        PhoneNumber,
        RelatedName,
        StreetAddress,
        URL
    )

    def __get_full_name(self):
        if hasattr(self, 'first_name') and hasattr(self, 'last_name'):
            return '%s %s' % (self.first_name, self.last_name)
        elif hasattr(self, 'first_name'):
            return '%s' % self.first_name
        else:
            return '%s' % self.last_name
    full_name = property(__get_full_name)

    def __get_is_person(self):
        if hasattr(self, 'display_as_company'):
            return self.display_as_company == 'person'
        else:
            return True
    is_person = property(__get_is_person)

    def __str__(self):
        if self.is_person:
            if hasattr(self, 'company_name'):
                return 'PERSON: %s: %s' % (self.full_name, self.company_name)
            else:
                return 'PERSON: %s' % self.full_name
        else:
            return 'COMPANY: %s' % self.company_name

    __repr__ = __str__

    def serialize(self, uuid):
        card = vobject.vCard()
        card.add('uid')
        card.uid.value = '%s@iphone-%s' % (self.id, uuid)

        #for id, group in self.groups.items():
            #card.add('categories')
            #card.categories.value = [child.data.name for child in children]

        if self.is_person:
            card.add('n')
            if hasattr(self, 'first_name') and hasattr(self, 'last_name'):
                card.n.value = vobject.vcard.Name(family=self.last_name,
                                                  given=self.first_name)
            elif hasattr(self, 'first_name'):
                card.n.value = vobject.vcard.Name(given=self.first_name)
            else:
                card.n.value = vobject.vcard.Name(family=self.last_name)
            card.add('fn')
            card.fn.value = '%s' % self.full_name

            if hasattr(self, 'company_name'):
                card.add('org')
                card.org.value = [self.company_name]
        else:
            card.add('org')
            card.org.value = [self.company_name]
            card.add('n')
            card.n.value = vobject.vcard.Name(given=self.first_name)
            card.add('fn')
            card.fn.value = self.first_name

        for id, phone in self.phone_numbers.items():
            phone.serialize(card)

        for id, address in self.street_addresses.items():
            address.serialize(card)

        for id, email in self.email_addresses.items():
            email.serialize(card)

        for id, im in self.ims.items():
            im.serialize(card)

        for id, url in self.urls.items():
            url.serialize(card)

        for id, date in self.dates.items():
            date.serialize(card)

        if hasattr(self, 'birthday'):
            card.add('bday')
            card.bday.value = self.birthday.strftime("%Y-%m-%d")

        if hasattr(self, 'image'):
            card.add('photo')
            card.photo.value = base64.b64encode(self.image)
            card.photo.params['ENCODING'] = ['BASE64']
            card.photo.params['TYPE'] = ['JPEG']

        if hasattr(self, "notes"):
            card.add('note')
            card.note.value = self.notes

        return card.serialize()

class Contacts(BaseList):
    parent_schema_name = "com.apple.Contacts"
    parent_schema_class = Contact

    state = state.contacts

    def __process_related_record(self, related_record):
        if isinstance(related_record, Group):
            for id in related_record.parent_ids:
                self._parent_records[id].groups[related_record.id] = related_record
        else:
            super(Contacts, self).__process_related_record(related_record)
