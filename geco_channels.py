#!/usr/bin/env python

import json
import re
# import sqlite3

# note to maintainers: please modify LAST_UPDATED and __version__ when
# changing anything. use the __run_tests__() method to make sure everything
# is working as expected.

__authors__ = ['Stefan Countryman']
DESC="""A script/module for querying timing channels. Reference is always made
to a physical layout, where Master/FanOut modules have slave devices connected
to them, and additional timing diagnostic devices exist. This is by analogy to
MEDM screens. All devices are represented internally as strings, which are kept
as close in form as possible to valid, descriptive EPICS channel names for
each device, in order to facilitate intuitive debugging, device comparisons,
and declarations of timing-system layout.
"""
# For the sake of consolodating code and avoiding dependency hell, this library
# also includes data about the current timing configuration at both sites. This
# is perhaps not the "nicest" way to do things, but is a good compromise given
# the fact that only aLIGO will use this library anyway.
__version__ = 0.3
LAST_UPDATED = 'Tue Jun 28 02:46:45 EDT 2016'
PORTS_PER_MFO = 16
# what types of slaves are there?
SLAVE_TYPES = ['CFC','DUOTONE','FANOUT','IRIGB','XOLOCK']
# can't use these characters in device types or descriptions, since they are
# used as delimiters in the internal string representation:
RESERVED_CHARS = set(';:,')
# what are the acceptable channel suffixes for each slave device? used to
# generate possible channel names for a given configuration.
CHANNEL_SUFFIXES = {
    'mfo_common': [
        'COMERR',
        'COMERRCOUNT',
        'CRCERR',
        'CRCERRCOUNT',
        'COMMISSING',
        'COMMISSCOUNT',
        'DOWNTIME',
        'COMCOUNT',
        'COMLENGTH',
        'DIP',
        'VCXOCTRL',
        'OCXOCTRL',
        'OCXOERR',
        'UPLINKDELAY',
        'EXTPPSDELAY',
        'GPSDELAY',
        'TIMINGTOLERANCE',
        'UPLINKUP',
        'USEUPLINK',
        'UPLINKLOS',
        'USEUPLINK',
        'UPLINKERRCOUNT',
        'UPLINKCRCERRCOUNT',
        'BOARDID',
        'BOARDREV',
        'SERIAL',
        'CODEID',
        'CODEREV',
        'GPS',
        'STRADDR',
        'NAME',
        'ISMASTER',
        'HASFANOUT',
        'FANOUTPORTS',
        'HASOCXO',
        'HASEXTPPS',
        'HASGPS',
        'USEEXT',
        'USEGPS',
        'USEUPLINK',
        'GPSLOCKED',
        'HASGPS',
        'OCXOLOCKED',
        'HASOCXO'
    ],
    'mfo_port_related': [
        'ACTIVE',
        'DELAYERR',
        'ERROR_FLAG',
        'LOS',
        'MEASUREDDELAY',
        'MISSING',
        'UP'
    ],
    'slave_common': [
        'SLAVE_ADDR',
        'SLAVE_BOARDID',
        'SLAVE_BOARDREV',
        'SLAVE_CODEID',
        'SLAVE_CODEREV',
        'SLAVE_DIP',
        'SLAVE_ERROR_FLAG',
        'SLAVE_ERROR_MSG',
        'SLAVE_GPS',
        'SLAVE_ID',
        'SLAVE_ISCFC',
        'SLAVE_ISDUOTONE',
        'SLAVE_ISFANOUT',
        'SLAVE_ISIRIGB',
        'SLAVE_ISXOLOCKING',
        'SLAVE_NAME',
        'SLAVE_SERIAL',
        'SLAVE_STRADDR',
        'SLAVE_UPLINKCRCERRCOUNT',
        'SLAVE_UPLINKERRCOUNT',
        'SLAVE_UPLINKLOS',
        'SLAVE_UPLINKUP',
        'SLAVE_VCXOCTRL'
    ],
    'CFC': [
        'SLAVE_CFC_FREQUENCY_1',
        'SLAVE_CFC_FREQUENCY_2',
        'SLAVE_CFC_FREQUENCY_3',
        'SLAVE_CFC_FREQUENCY_4',
        'SLAVE_CFC_FREQUENCY_5',
        'SLAVE_CFC_FREQUENCY_6',
        'SLAVE_CFC_HASINPUT',
        'SLAVE_CFC_TIMEDIFF_1',
        'SLAVE_CFC_TIMEDIFF_2',
        'SLAVE_CFC_TIMEDIFF_3',
        'SLAVE_CFC_TIMEDIFF_4',
        'SLAVE_CFC_TIMEDIFF_5',
        'SLAVE_CFC_TIMEDIFF_6',
        'SLAVE_CFC_TIMEDIFF_7'
    ],
    'DUOTONE': [
    ],
    'FANOUT': [
        'SLAVE_FANOUT_DELAYERR',
        'SLAVE_FANOUT_EXTPPSDELAY',
        'SLAVE_FANOUT_FANOUTLOS',
        'SLAVE_FANOUT_FANOUTPORTS',
        'SLAVE_FANOUT_FANOUTUP',
        'SLAVE_FANOUT_GPSDELAY',
        'SLAVE_FANOUT_GPSERR',
        'SLAVE_FANOUT_GPSERRCOUNT',
        'SLAVE_FANOUT_GPSLOCKED',
        'SLAVE_FANOUT_HASEXTPPS',
        'SLAVE_FANOUT_HASFANOUT',
        'SLAVE_FANOUT_HASGPS',
        'SLAVE_FANOUT_HASOCXO',
        'SLAVE_FANOUT_ISMASTER',
        'SLAVE_FANOUT_MISSING',
        'SLAVE_FANOUT_OCXOCTRL',
        'SLAVE_FANOUT_OCXOERR',
        'SLAVE_FANOUT_OCXOLOCKED',
        'SLAVE_FANOUT_UPLINKDELAY',
        'SLAVE_FANOUT_USEEXT',
        'SLAVE_FANOUT_USEGPS',
        'SLAVE_FANOUT_USEUPLINK'
    ],
    'IRIGB': [
        'SLAVE_IRIGB_DST',
        'SLAVE_IRIGB_IRIGDIFFA',
        'SLAVE_IRIGB_IRIGDIFFB',
        'SLAVE_IRIGB_IRIGDIFFC',
        'SLAVE_IRIGB_IRIGERRCOUNTA',
        'SLAVE_IRIGB_IRIGERRCOUNTB',
        'SLAVE_IRIGB_IRIGERRCOUNTC',
        'SLAVE_IRIGB_LEAPPEND',
        'SLAVE_IRIGB_LEAPSEC',
        'SLAVE_IRIGB_LEAPSUB',
        'SLAVE_IRIGB_TIMEZONE'
    ],
    'XOLOCK': [
        'SLAVE_XOLOCK_HASOCXO',
        'SLAVE_XOLOCK_MEASUREDFREQ',
        'SLAVE_XOLOCK_OCXOCTRL',
        'SLAVE_XOLOCK_OCXOERR',
        'SLAVE_XOLOCK_OCXOLOCKED',
        'SLAVE_XOLOCK_PRESETFREQ'
    ]
}

class MEDMScreen(str):
    """An abstract class for strings representing MEDM screens.
    """
    def get_own_channels(self):
        """Return a list of all channels in use by this device but not its
        children."""
        return []
    def get_child_channels(self):
        """Return a list of all channels in use by this device's child
        devices, if they exist (otherwise, return an empty list)."""
        return []
    def get_channels(self):
        """Return a list of all channels in use by this device as well as any
        connected child devices."""
        return self.get_own_channels() + self.get_child_channels()

class TopMEDMScreen(MEDMScreen):
    """An abstract class for strings representing top-level MEDM screens.
    """

class TimingSlave(MEDMScreen):
    """Any type of device that can get its timing signal from a timing
    Master/FanOut. Is represented as a string starting with the string
    representation of the MFO to which is connected and ending with a colon
    followed by the port this Slave connects to. For example, a DuoTone
    connected to the first port (port 0) of a Master (with no other devices
    connected) is represented by:

        'H1:SYS-TIMING_C_MA_A;:DUOTONE;,;,;,;,;,;,;,;,;,;,;,;,;,;,;,;:0'

    If a TimingSlave is set at a port on the MFO where no device is connected,
    as in the following example, the resulting TimingSlave will have a
    dev_type set to None.

        'H1:SYS-TIMING_C_MA_A;:DUOTONE;,;,;,;,;,;,;,;,;,;,;,;,;,;,;,;:1'

    """
    def mfo(self):
        """Return the Master/FanOut that this timing slave is connected to."""
        return MFO(':'.join(self.split(':')[0:3]))
    def port_number(self):
        """Return the number of the port on the Master/FanOut that this Timing
        Slave device is connected to."""
        return int(self.split(':')[3])
    def __dev__(self):
        """Split up this device's string into device type and, if included, a
        device description."""
        return self.split(':')[2].split(',')[self.port_number()].split(';')
    def dev_type(self):
        """Get the device type of this Timing Slave."""
        dev_type = self.__dev__()[0]
        if dev_type == '':
            return None
        else:
            if dev_type in SLAVE_TYPES:
                return dev_type
            else:
                raise ValueError('Not a Timing Slave device type: ' + dev_type)
    def description(self):
        """Get the description for this Timing Slave, if it exists. If this
        device does not exist, return None. If this device has no description,
        return an empty string."""
        if self.dev_type() is None:
            return None
        else:
            dev = self.__dev__()
            if len(dev) == 2:
                return dev[1]
            else:
                raise ValueError('Wrong number of items in device string: ' 
                                 + ';'.join(dev))
    def get_own_channels(self):
        """Return a list of all channel names associated with this Timing Slave
        (note that, if this slave happens to be a FanOut, it will have its
        own diagnostic channels, along with channels for its own Slaves; these
        will only be accessible if the fanout is treated separately as an MFO.
        This parallels the way channels and devices are treated in MEDM screens
        on site.)"""
        suffixes = []
        suffixes += CHANNEL_SUFFIXES['slave_common']
        suffixes += CHANNEL_SUFFIXES[self.dev_type()]
        return [self.mfo().portless_name() + '_PORT_' + str(self.port_number())
                + '_' + x for x in suffixes]
    def name(self):
        """Return a string which describes this device in human-readable form
        but which does not uniquely specify its MFO configuration nor provide
        the basis for generating usable EPICS channel names (though it does
        come close)."""
        return (self.mfo().portless_name() + '_PORT_' + str(self.port_number())
                + '_SLAVE_' + self.dev_type())

class MFO(TopMEDMScreen):
    """A Master/FanOut device, as seen in MEDM screens. This type of object
    also uniquely specifies the devices connected to this MFO's ports using
    a comma-delimited list of connected devices following a colon at the end of
    the string representation. An example with a DuoTone connected to port 0
    and FanOut connected to port 4 looks like:

        'H1:SYS-TIMING_C_MA_A;:DUOTONE;,;,;,;,;FANOUT;,;,;,;,;,;,;,;,;,;,;,;'

    Each Timing Slave can have an optional description following the device
    type and separated with a semicolon. Note that this description cannot
    contain the following characters:

        ;:,

    since they are used syntactically within the string. Starting from the
    above example, the FanOut connected to port 4 could be described as "test
    stand" using the following string:

        'H1:SYS-TIMING_C_MA_A;:;,;,;,;,;FANOUT;test stand,;,;,;,;,;,;,;,;,;,;,;'

    The MFO itself can also have a device description, given after the portless
    name of the MFO and separated by a semicolon, as in the following:

        'H1:SYS-TIMING_C_MA_A;corner msr:,;,;,;,;FANOUT;,;,;,;,;,;,;,;,;,;,;,;'

    Even if a description is not present, the semicolons remain in place to
    ensure the uniqueness of any given string representation.
    """
    def ifo(self):
        """Return the Interferometer for the MFO that this string describes."""
        return self.split(':')[0]
    def subsystem(self):
        """Return the Subsystem (should be SYS-TIMING) for the MFO that this
        string describes."""
        return self.split(':')[1].split('_')[0]
    def location(self):
        """Return the Location (Corner Station, X-End, or Y-End) for the MFO
        that this string describes."""
        return self.split(':')[1].split('_')[1]
    def m_or_f(self):
        """Return whether the MFO that this string describes is a Master (M) or
        FanOut (F)."""
        return self.split(':')[1].split('_')[2]
    def dev_id(self):
        """There can be multiple FanOuts in a given location. We distinguish
        between them by assigning letters, starting at A. Return the device ID
        letter for the device that this string describes."""
        # Make sure to leave out the description for this MFO, which can follow
        # the dev_id and is separated by a semicolon (when present).
        return self.split(':')[1].split('_')[3].split(';')[0]
    def port(self, start=None, stop=None, step=None):
        """There are 16 ports, numbered 0-15, to which Timing Slave modules can
        be connected by fiber link. Return the Timing Slavee connected to a
        particular port. A slice of ports can be taken using syntax similar to
        that of range(start(, stop(, step))), where out-of-bounds indices are
        automatically and silently truncated and a list of results is returned.
        If no argument is given, return all devices."""
        if start is None:
            return [TimingSlave(str(self) + ':' + str(i))
                    for i in range(0, PORTS_PER_MFO)]
        if stop is None:
            return TimingSlave(str(self) + ':' + str(start))
        else:
            if step is None:
                step = 1
            if stop > PORTS_PER_MFO:
                stop = PORTS_PER_MFO
            if start < 0:
                start = 0
            return [TimingSlave(str(self) + ':' + str(i))
                    for i in range(start, stop, step)]
    def portless_name(self):
        """Return a string representing this MFO but with no information about
        used ports and no channel description. This is not a valid MFO object,
        but can be used to construct valid EPICS channels."""
        # the last bit involving the semicolong ensures that we don't return
        # the channel description (if it is present).
        return ':'.join(self.split(':')[0:2]).split(';')[0]
    def description(self):
        """If this MFO has a description string, return it. Otherwise, return
        an empty string."""
        mfo_list = ':'.join(self.split(':')[0:2]).split(';')
        if len(mfo_list) == 2:
            return mfo_list[1]
        else:
            raise ValueError('Wrong number of items in mfo string: ' 
                                + ';'.join(dev))
    def get_own_channels(self):
        """Get a list of channels related to this MFO, ignoring any channels
        related to Timing Slave devices attached to this MFO."""
        suffixes = []
        suffixes += CHANNEL_SUFFIXES['mfo_common']
        for i in range(PORTS_PER_MFO):
            suffixes += ['PORT_' + str(i) + '_' + x for x in
                         CHANNEL_SUFFIXES['mfo_port_related']]
        prefix = self.portless_name() + '_'
        return [prefix + suffix for suffix in suffixes]
    def get_child_channels(self):
        """Get a list of channels in use by this MFO's attached slaves. Does
        not include channels relating to this MFO; returns only Slave-related
        channels."""
        channels = []
        for i in range(PORTS_PER_MFO):
            slave = self.port(i)
            if not slave.dev_type() is None:
                channels += slave.get_channels()
        return channels
    def slave_types(self):
        """Return a set of slave types connected to this device."""
        return set([slave.dev_type() for slave in self.port()])
    def used_ports(self):
        """Return a list of ports used by this device."""
        res = []
        for slave in self.port():
            if not slave.dev_type() is None:
                res.append(slave.port_number())
        return res
    def to_dict(self):
        """Return a dictionary representing this MFO. good for implementing
        various serialization strategies."""
        return {
            'ifo': self.ifo(),
            'subsystem': self.subsystem(),
            'location': self.location(),
            'm_or_f': self.m_or_f(),
            'dev_id': self.dev_id(),
            'description': self.description(),
            'ports': [{
                'dev_type': self.port(i).dev_type(),
                'description': self.port(i).description()
            } for i in range(PORTS_PER_MFO)]
        }
    def to_json(self):
        """Return a pretty-formatted JSON string representing this MFO."""
        return json.dumps(self.to_dict(), indent=4, separators=(',', ': '))
    @classmethod
    def from_dict(cls, d):
        """Construct an MFO object from a dictionary."""
        mfo_str = (d['ifo'] + ':' + '_'.join([d['subsystem'], d['location'],
                                         d['m_or_f'],d['dev_id']])
             + ';' + d['description'] + ':')
        # unused ports show up as None, but are represented as empty strings
        ports = []
        for p in d['ports']:
            if p['dev_type'] is None and p['description'] is None:
                ports.append({'dev_type': '', 'description': ''})
            elif p['dev_type'] is None or p['description'] is None:
                raise ValueError(('Bad MFO description: either dev_type and '
                                  'description are both None, or both are '
                                  'nonempty strings.'))
            elif any((c in RESERVED_CHARS) for c in p['dev_type']):
                raise ValueError(('Cannot use reserved chars '
                                  + ''.join(RESERVED_CHARS)
                                  + ' in dev_type: ' + p['dev_type']))
            elif any((c in RESERVED_CHARS) for c in p['description']):
                raise ValueError(('Cannot use reserved chars '
                                  + ''.join(RESERVED_CHARS)
                                  + ' in description: ' + p['description']))
            else:
                ports.append({'dev_type':    p['dev_type'],
                              'description': p['description']})
        ports_str = [p['dev_type'] + ';' + p['description']
                     for p in ports]
        port_str = ','.join(ports_str)
        return cls(mfo_str + port_str)
    @classmethod
    def from_json(cls, json_str):
        """Construct an MFO object from a JSON-formatted string."""
        return cls.from_dict(json.loads(json_str))

def lho_timing_system():
    """Return a list of top-level MEDM objects representing the timing
    system as installed at LIGO Hanford Observatory (LHO)."""
    return [
        MFO.from_dict({
            "description": "LHO Master in Corner Main Storage Room (MSR)",
            "subsystem": "SYS-TIMING",
            "dev_id": "A",
            "location": "C",
            "ifo": "H1",
            "ports": [
                {
                    "dev_type": "IRIGB",
                    "description": "IRIG-B"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "CFC",
                    "description": "Comparator"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "FANOUT",
                    "description": "CER-SUS C_FO_B"
                },
                {
                    "dev_type": "FANOUT",
                    "description": "CER-ISC C_FO_A"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "MX"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "MY"
                },
                {
                    "dev_type": "FANOUT",
                    "description": "EX X_FO_A"
                },
                {
                    "dev_type": "FANOUT",
                    "description": "EY Y_FO_A"
                }
            ],
            "m_or_f": "MA"
        }),
        MFO.from_dict({
            "description": "LHO FanOut in X-End Station Receiving (EX)",
            "subsystem": "SYS-TIMING",
            "dev_id": "A",
            "location": "X",
            "ifo": "H1",
            "ports": [
                {
                    "dev_type": "IRIGB",
                    "description": "IRIG-B"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXEX"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSEX"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIEX"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "ISCEX"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF24.4"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF70.0"
                },
                {
                    "dev_type": "CFC",
                    "description": "Comparator"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                }
            ],
            "m_or_f": "FO"
        }),
        MFO.from_dict({
            "description": "LHO FanOut in Y-End Station Receiving (EY)",
            "subsystem": "SYS-TIMING",
            "dev_id": "A",
            "location": "Y",
            "ifo": "H1",
            "ports": [
                {
                    "dev_type": "IRIGB",
                    "description": "IRIG-B"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXEY"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSEY"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIEY"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "ISCEY"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF24.4"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF70.0"
                },
                {
                    "dev_type": "CFC",
                    "description": "Comparator"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                }
            ],
            "m_or_f": "FO"
        }),
        MFO.from_dict({
            "description": "LHO FanOut B in CER",
            "subsystem": "SYS-TIMING",
            "dev_id": "B",
            "location": "C",
            "ifo": "H1",
            "ports": [
                {
                    "dev_type": "DUOTONE",
                    "description": "PSL0"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "OAF0"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXH2"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXH34"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXH56"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXB123"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSH2A"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSH2B"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSH34"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSH56"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSB123"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIH16"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIH23"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                }
            ],
            "m_or_f": "FO"
        }),
        MFO.from_dict({
            "description": "LHO FanOut A in CER",
            "subsystem": "SYS-TIMING",
            "dev_id": "A",
            "location": "C",
            "ifo": "H1",
            "ports": [
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIH45"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIB1"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIB2"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIB3"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "LSC0"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "ASC0"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF21.5"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF24.0"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF35.5"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF71.0"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF80.0"
                },
                {
                    "dev_type": "CFC",
                    "description": "Comparator"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                }
            ],
            "m_or_f": "FO"
        })
    ]

def llo_timing_system():
    """Return a list of top-level MEDM objects representing the timing
    system as installed at LIGO Livingston Observatory (LLO)."""
    return [
        MFO.from_dict({
            "description": "LLO Master in Corner Main Storage Room (MSR)",
            "subsystem": "SYS-TIMING",
            "dev_id": "A",
            "location": "C",
            "ifo": "L1",
            "ports": [
                {
                    "dev_type": "IRIGB",
                    "description": "IRIG-B"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "CFC",
                    "description": "Comparator"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "FANOUT",
                    "description": "CER-SUS C_FO_B"
                },
                {
                    "dev_type": "FANOUT",
                    "description": "CER-ISC C_FO_A"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "FANOUT",
                    "description": "Test Stand FanOut"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "FANOUT",
                    "description": "EX X_FO_A"
                },
                {
                    "dev_type": "FANOUT",
                    "description": "EY Y_FO_A"
                }
            ],
            "m_or_f": "MA"
        }),
        MFO.from_dict({
            "description": "LLO FanOut in X-End Station Receiving (EX)",
            "subsystem": "SYS-TIMING",
            "dev_id": "A",
            "location": "X",
            "ifo": "L1",
            "ports": [
                {
                    "dev_type": "IRIGB",
                    "description": "IRIG-B"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXEX"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSEX"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIEX"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "ISCEX"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF24.4"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF70.0"
                },
                {
                    "dev_type": "CFC",
                    "description": "Comparator"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                }
            ],
            "m_or_f": "FO"
        }),
        MFO.from_dict({
            "description": "LLO FanOut in Y-End Station Receiving (EY)",
            "subsystem": "SYS-TIMING",
            "dev_id": "A",
            "location": "Y",
            "ifo": "L1",
            "ports": [
                {
                    "dev_type": "IRIGB",
                    "description": "IRIG-B"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXEY"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSEY"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIEY"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "ISCEY"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF24.4"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF70.0"
                },
                {
                    "dev_type": "CFC",
                    "description": "Comparator"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                }
            ],
            "m_or_f": "FO"
        }),
        MFO.from_dict({
            "description": "LLO FanOut B in CER",
            "subsystem": "SYS-TIMING",
            "dev_id": "B",
            "location": "C",
            "ifo": "L1",
            "ports": [
                {
                    "dev_type": "DUOTONE",
                    "description": "PSL0"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "OAF0"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXH2"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXH34"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXH56"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSAUXB123"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSH2A"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSH2B"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSH34"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSH56"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SUSB123"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIH16"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIH23"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                }
            ],
            "m_or_f": "FO"
        }),
        MFO.from_dict({
            "description": "LLO FanOut A in CER",
            "subsystem": "SYS-TIMING",
            "dev_id": "A",
            "location": "C",
            "ifo": "L1",
            "ports": [
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIH45"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIB1"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIB2"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "SEIB3"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "LSC0"
                },
                {
                    "dev_type": "DUOTONE",
                    "description": "ASC0"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF21.5"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF24.0"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF35.5"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF71.0"
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF80.0"
                },
                {
                    "dev_type": "CFC",
                    "description": "Comparator"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": "XOLOCK",
                    "description": "RF80.0"
                },
                {
                    "dev_type": None,
                    "description": None
                },
                {
                    "dev_type": None,
                    "description": None
                }
            ],
            "m_or_f": "FO"
        })
    ]

def aligo_timing_system():
    """Return a list of top-level MEDM objects representing the timing
    system as installed at all LIGO observatories."""
    return lho_timing_system() + llo_timing_system()

# and now, a pair of classes that will allow us to handily avoid using SQL
class DevList(list):
    """A class for applying filters to lists of timing devices."""
    def select(self, dev_type=object):
        return DevListSelector(self, dev_type)

class DevListSelector(object):
    """A class that specifies a specific type to which members of a DevList
    should belong, and which provides a function for implementing that
    restriction while narrowing search results using a list of parameters and
    their required values. Basically just exists to allow for the nice syntax

        DevList(stuff).select(MFO).by('ifo=h')

    which allows for easier querying. If by() is called with no constraints,
    with empty argument strings, or with constraints equal to the wildcard
    symbol '*' (like below):

        # all will be equal to DevList(stuff)
        DevList(stuff).select(MFO).by('ifo=*')
        DevList(stuff).select(MFO).by('')
        DevList(stuff).select(MFO).by()
        DevList(stuff).select(MFO).cancel()

    then no selection occurs and the original DevList is returned (equivalent
    to calling cancel()). If no filter on constraints is made, but only
    a specific type of device is desired in the DevList, call only():

        DevList(stuff).select(MFO).only()

    will return the same DevList but with all non-MFO instances removed.
    """
    def __init__(self, dev_list, dev_type):
        if not isinstance(dev_list, DevList):
            raise ValueError('DevListSelector can only select DevList.')
        self.dev_list = dev_list
        self.dev_type = dev_type
    def cancel(self):
        """Cancel this selection and return the original DevList, with no
        constraints applied."""
        return self.dev_list
    def only(self):
        """Apply the type constraint specified by this selector without
        applying further parameter constraints."""
        res = DevList()
        for dev in self.dev_list:
            if isinstance(dev, self.dev_type):
                res.append(dev)
        return res
    def by(self, *constraints):
        """Only devices in DevListSelector's DevList which match the given
        constraints and the required type will be returned if nontrivial
        constraints are given. If the constraint strings are empty, or if
        the constraints are set equal to a wildcard '*', or if no constraints
        are given, then the original DevList is returned with no changes."""
        if len(constraints) == 0:
            return self.cancel()
        if len(constraints) == 1:
            constraint = constraints[0]
            if constraint == '':
                return self.cancel()
            # can apply any of these comparators
            if '!=' in constraint:
                (param, val) = re.split('[ \t]*!=[ \t]*', constraint)
                test = lambda a, b: a != b
            elif '>=' in constraint:
                (param, val) = re.split('[ \t]*>=[ \t]*', constraint)
                test = lambda a, b: a >= b
            elif '<=' in constraint:
                (param, val) = re.split('[ \t]*<=[ \t]*', constraint)
                test = lambda a, b: a <= b
            elif '=' in constraint:
                (param, val) = re.split('[ \t]*=[ \t]*', constraint)
                test = lambda a, b: a == b
            elif '>' in constraint:
                (param, val) = re.split('[ \t]*>[ \t]*', constraint)
                test = lambda a, b: a > b
            elif '<' in constraint:
                (param, val) = re.split('[ \t]*<[ \t]*', constraint)
                test = lambda a, b: a < b
            elif bool(re.search('[ \t]IN[ \t]', constraint)):
                (param, val) = re.split('[ \t]+IN[ \t]+', constraint)
                test = lambda a, b: a in b
            elif bool(re.search('[ \t]CONTAINS[ \t]', constraint)):
                (param, val) = re.split('[ \t]+CONTAINS[ \t]+', constraint)
                test = lambda a, b: b in a
            else:
                raise ValueError('This is a no good constraint, pal: ' +
                                 str(constraint))
            if val == '*':
                return self.cancel()
            else:
                val = val.upper()   # case insensitive
                res = DevList()
                for dev in self.only():
                    if test(str(dev.__getattribute__(param)()).upper(), val):
                        res.append(dev)
                return res
        else:
            constraint = constraints[0]
            the_rest = constraints[1:]
            return self.by(constraint).select(self.dev_type).by(*the_rest)

def __run_tests__():
    """Run tests to confirm that the script is behaving as expected."""
    # serializing and deserializing is a good way to make sure all is well.
    for d in aligo_timing_system():
        if MFO.from_json(d.to_json()) != d:
            raise AssertionError(('Serializing and deserializing changed '
                                  'representation of MFO: ' + str(d) + ' vs. '
                                  + str(MFO.from_json(d.to_json()))))
        # make sure we catch bad description and dev_type input in our
        # deserializer
        for bad_char in RESERVED_CHARS:
            dic1 = d.to_dict()
            dic2 = d.to_dict()
            dic1['ports'][0]['dev_type'] += bad_char + 'stuff'
            dic2['ports'][0]['description'] += bad_char + 'stuff'
            try:
                MFO.from_dict(dic1)
                raise AssertionError(('Bad character in dev_type allowed '
                                      'through from_dict method: ' + bad_char))
            except ValueError:
                # a ValueError was thrown, as desired.
                pass
            try:
                MFO.from_dict(dic2)
                raise AssertionError(('Bad character in description allowed '
                                      'through from_dict method: ' + bad_char))
            except ValueError:
                # a ValueError was thrown, as desired.
                pass
    return True

# if running from the command line, we should run this stuff
def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(description=(DESC + 
                                     'When called from the command line, '
                                     'query against channel names '
                                     'used by the aLIGO timing system and '
                                     'return a newline-delimited list of '
                                     'matching channel names.'),
                                     epilog=('NOTE: queries will currently '
                                             'only return results related to '
                                             'the Timing Distribution System. '
                                             'Timing Diagnostic System '
                                             'channels will be added in a '
                                             'future release. This includes '
                                             'ADC channels that are part of '
                                             'the CAL subsystem.'))
    parser.add_argument('-i','--ifo',
                        help=('Interferometer; "h1" is Hanford, "l1" is '
                             'Livingston. DEFAULT: *'),
                        choices=['h1','l1','*'], default='*')
    parser.add_argument('-s','--subsystem',
                        help=('Most timing belongs to "SYS-TIMING", but some '
                             'channels are in other subsystems. DEFAULT: *'),
                        choices=['SYS-TIMING','*'], default='*')
    parser.add_argument('-l','--location',
                        help=('Location; "c" is corner station, "x" is X end '
                             'station, "y" is Y end station. DEFAULT: *'),
                        choices=['c','x','y','*'], default='*')
    parser.add_argument('-m','--master_or_fanout',
                        help=('Is this device connected to a Master or FanOut '
                             'board? "ma" specifies a Master, "fo" a FanOut.'
                             'DEFAULT: *'),
                        choices=['ma','fo','*'], default='*')
    parser.add_argument('-d','--device_id',
                        help=('"a", "b"... etc. specifies which FanOut (or '
                             'Master) this device connects to (since there '
                             'can be multiple FanOuts at a given location.'
                             'DEFAULT: *'),
                        choices=['a','b','c','*'], default='*')
    parser.add_argument('-p','--port_number',
                        help=('The port number on the MFO to which this device '
                             'connects. DEFAULT: *'),
                        choices=[str(p) for p in range(PORTS_PER_MFO)] + ['*'],
                        default='*')
    parser.add_argument('-t','--dev_type',
                        help=('The device type. IRIG-B Module (irigb), '
                             'RFOscillator/oscillator locking (xolock), '
                             'Slave/DuoTone assembly (duotone), '
                             'Timing Comparator Module (cfc), or '
                             'a fanout module (fanout). DEFAULT: *'),
                        choices=['irigb','xolock','duotone','cfc',
                                 'fanout','*'],
                        default='*')
    parser.add_argument('-q','--query_type',
                        help=('What type of query is this? Can return a list '
                              'of all matching channels (c), a list of only '
                              'MFO-specific matching channels (cm), a list of '
                              'only Timing-Slave-specific matching channels '
                              '(cs), a list of descriptive strings for '
                              'matching MFO devices (m), or a list of '
                              'descriptive strings for matching Timing Slave '
                              'devices (s). DEFAULT: c'),
                        choices=['c','cm','cs','m','s'], default='c')
    return parser.parse_args()

def main():
    args = parse_args()
    def constrain_mfo(args):
        return DevList(aligo_timing_system()).select(MFO).by(
            'ifo='+args.ifo,
            'subsystem='+args.subsystem,
            'location='+args.location,
            'm_or_f='+args.master_or_fanout,
            'dev_id='+args.device_id,
            'slave_types CONTAINS '+args.dev_type,
            'used_ports CONTAINS '+args.port_number)
    def constrain_slave(args):
        slaves = DevList()
        for mfo in constrain_mfo(args):
            slaves += mfo.port()
        return slaves.select(TimingSlave).by(
            'dev_type!=None',
            'port_number='+args.port_number,
            'dev_type='+args.dev_type)
    # deal with each specific query_type
    if args.query_type == 'm':
        for mfo in constrain_mfo(args):
            print(mfo.portless_name())
    if args.query_type == 's':
        for slave in constrain_slave(args):
            print(slave.name())
    if args.query_type == 'c' or args.query_type == 'cm':
        for mfo in constrain_mfo(args):
            for ch in mfo.get_own_channels():
                print(ch)
    if args.query_type == 'c' or args.query_type == 'cs':
        for slave in constrain_slave(args):
            for ch in slave.get_own_channels():
                print(ch)

if __name__ == "__main__":
    main()

