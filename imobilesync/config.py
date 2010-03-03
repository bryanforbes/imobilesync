from imobilesync.path import path
from ConfigParser import ConfigParser
from datetime import datetime
import os, cPickle

__all__ = ['Config', 'State']

_home = path(os.environ.get('HOME', '/'))

data_directory = path(os.environ.get('XDG_DATA_HOME',
			_home / '.local' / 'share')) / 'imobilesync'
config_directory = path(os.environ.get('XDG_CONFIG_HOME',
    _home / '.config')) / 'imobilesync'

class Bunch(dict):
    """A dictionary that provides attribute-style access."""

    def add(self, section, defaults=None):
        if not hasattr(self, section):
            if defaults is not None:
                setattr(self, section, Bunch(**defaults))
            else:
                setattr(self, section, Bunch())
        return getattr(self, section)

    def __repr__(self):
        keys = self.keys()
        keys.sort()
        args = ', '.join(['%s=%r' % (key, self[key]) for key in keys])
        return '%s(%s)' % (self.__class__.__name__, args)
    
    def __getitem__(self, key):
        item = dict.__getitem__(self, key)
        if callable(item):
            return item()
        return item

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    __setattr__ = dict.__setitem__

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)

class Config(Bunch):
    config_file = config_directory / 'config.ini'

    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

        self.contacts = Bunch()
        self.calendars = Bunch()

    def write(self):
        if not self.config_directory.exists():
            self.config_directory.makedirs()

        file = self.config_file.open('w')

        cp = ConfigParser()
        cp.add_section('contacts')
        cp.add_section('calendars')

        for key, value in self.contacts.items():
            cp.set('contacts', key, value)

        for key, value in self.calendars.items():
            cp.set('calendars', key, value)

        cp.write(file)
        file.close()

    @classmethod
    def load(cls):
        obj = cls()
        if not config_directory.exists() and not cls.config_file.exists():
            return obj

        cp = ConfigParser()
        cp.read(cls.config_file)

        obj.contacts.update(cp.items("contacts"))
        obj.calendars.update(cp.items("calendars"))

        return obj

class State(Bunch):
    state_file = config_directory / 'state.pickle'

    def write(self):
        if not config_directory.exists():
            config_directory.makedirs()

        cPickle.dump(self, self.state_file.open('w'))

    @classmethod
    def load(cls):
        if not config_directory.exists() or not cls.state_file.exists():
            return State()
        else:
            return cPickle.load(cls.state_file.open('r'))

config = Config.load()
state = State.load()
