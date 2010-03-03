from imobilesync.data.base import BaseList, Base, RelatedBase
from imobilesync.config import state, config
from imobilesync.options import parser

import vobject, datetime

__all__ = ['Calendar', 'Calendars']

class CalendarRelated(RelatedBase):
    parent_key = 'calendar'

class EventRelated(RelatedBase):
    parent_key = 'owner'

class Attendee(EventRelated):
    entity_name = 'com.apple.calendars.Attendee'
    parent_prop = 'attendees'

class AlarmBase(EventRelated):
    def get_ical_type(self):
        pass

    def serialize(self, event, summary):
        alarm = event.add('valarm')
        alarm.add('action').value = self.get_ical_type()

        if summary:
            alarm.add('description').value = summary

        if hasattr(self, 'triggerduration'):
            trigger = alarm.add('trigger')
            # Convert from the silly unsigned int represent a signed int
            if self.triggerduration == 0:
                trigger.value = datetime.timedelta(seconds=0)
            else:
                trigger.value = datetime.timedelta(seconds=-((2**64) - self.triggerduration))
            trigger.params['RELATED'] = ['START']

class AudioAlarm(AlarmBase):
    entity_name = 'com.apple.calendars.AudioAlarm'
    parent_prop = 'audioalarms'

    def get_ical_type(self):
        return 'AUDIO'

class DisplayAlarm(AlarmBase):
    entity_name = 'com.apple.calendars.DisplayAlarm'
    parent_prop = 'displayalarms'

    def get_ical_type(self):
        return 'DISPLAY'

class Organizer(EventRelated):
    entity_name = 'com.apple.calendars.Organizer'
    parent_prop = 'organizer'

class Recurrence(EventRelated):
    entity_name = 'com.apple.calendars.Recurrence'
    parent_prop = 'recurrences'

    def serialize(self, event):
        rrule = ''
        if hasattr(self, 'frequency') and self.frequency:
            rrule += 'FREQ=%s;' % self.frequency.upper()
        if hasattr(self, 'interval') and self.interval:
            rrule += 'INTERVAL=%s;' % self.interval
        if hasattr(self, 'bymonth') and self.bymonth:
            rrule += 'BYMONTH=%s;' % self.bymonth
        if hasattr(self, 'bymonthday') and self.bymonthday:
            rrule += 'BYMONTHDAY=%s;' % self.bymonthday

        if rrule:
            event.add('rrule').value = rrule

class Event(CalendarRelated):
    entity_name = 'com.apple.calendars.Event'
    parent_prop = 'events'

    related_classes = (
        Attendee,
        AudioAlarm,
        DisplayAlarm,
        Organizer,
        Recurrence
    )

    def serialize(self, cal):
        event = cal.add('vevent')
        event.add('uid').value = self.uuid

        if hasattr(self, 'all_day'):
            event.add('dtstart').value = self.start_date.date()
            event.add('dtend').value = self.end_date.date()
        else:
            event.add('dtstart').value = self.start_date
            event.add('dtend').value = self.end_date

        if self.summary:
            event.add('summary')
            event.summary.value = self.summary

        if hasattr(self, 'location'):
            event.add('location')
            event.location.value = self.location

        if hasattr(self, 'description'):
            event.add('description')
            event.description.value = self.description

        for id, recurrence in self.recurrences.items():
            recurrence.serialize(event)

        for id, alarm in self.displayalarms.items():
            alarm.serialize(event, self.summary)

        for id, alarm in self.audioalarms.items():
            alarm.serialize(event, self.summary)

class Calendar(Base):
    entity_name = 'com.apple.calendars.Calendar'

    related_classes = (
        Event,
    )

    def __str__(self):
        return 'Calendar: %s' % self.title
    __repr__ = __str__

    def __ical__(self):
        cal = vobject.iCalendar()
        title = cal.add('X-WR-CALNAME')
        title.value = self.title

        for id, event in self.events.items():
            event.serialize(cal)
        return cal

    def serialize(self):
        return self.__ical__().serialize()

class Calendars(BaseList):
    parent_schema_name = "com.apple.Calendars"
    parent_schema_class = Calendar

    config = config.add('calendars', {})
    state = state.add('calendars', {
        'last_sync_time': None
    })

    def __init__(self, uuid, mobile_sync):
        super(Calendars, self).__init__(uuid, mobile_sync)

        self._event_records = {}
        self.__event_class_map = {}
        for cls in Event.related_classes:
            self.__event_class_map[cls.entity_name] = cls

    def _process_record(self, entity_name, id, record):
        super(Calendars, self)._process_record(entity_name, id, record)
        if entity_name in self.__event_class_map:
            cls = self.__event_class_map[entity_name]
            obj = cls(self._uuid, id, record)

            self._process_related_record(obj)

    def _process_related_record(self, related_record):
        if isinstance(related_record, Event):
            self._event_records[related_record.id] = related_record
            super(Calendars, self)._process_related_record(related_record)
        elif isinstance(related_record, Calendar):
            super(Calendars, self)._process_related_record(related_record)
        else:
            parent_objs = getattr(self._event_records[related_record.parent_id], related_record.parent_prop)
            parent_objs[related_record.id] = related_record

parser.add_option('--calendars', action='append_const', dest='sync_type', const=Calendars)
