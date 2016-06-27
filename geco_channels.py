#!/usr/bin/env python

# a script/module for querying timing channels.

import argparse

__version__ = 0.0
PORTS_PER_MFO = 16
#types of slaves are there?
SLAVE_TYPES = ['CFC','DUOTONE','FANOUT','IRIGB','XOLOCK']
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


class TimingSlave(object):
    """Any type of device that can get its timing signal from a timing
    Master/FanOut.
    """
    def __init__(self, dev_type, mfo, port_number, description=''):
        if dev_type in SLAVE_TYPES:
            self.type = dev_type
        else:
            raise ValueError('Not a Timing Slave device type: ' + dev_type)
        self.mfo = mfo
        self.port_number = port_number
        self.description = description
    def get_channels(self):
        """Return a list of all channel names associated with this Timing Slave
        (note that, if this slave happens to be a FanOut, it will have its
        own diagnostic channels, along with channels for its own Slaves; these
        will only be accessible if the fanout is treated separately as an MFO.
        This parallels the way channels and devices are treated in MEDM screens
        on site.)"""
        suffixes = CHANNEL_SUFFIXES['slave_common']
        suffixes += CHANNEL_SUFFIXES[self.type]
        return [self.mfo.portless_name() + '_PORT_' + self.port_number +
                x for x in suffixes]

class MEDMScreen(str):
    """An abstract class for strings representing top-level MEDM screens.
    """

class MFO(MEDMScreen):
    """A Master/FanOut device, as seen in MEDM screens. This type of object
    also uniquely specifies the devices connected to this MFO's ports using
    a comma-delimited list of connected devices following a colon at the end of
    the string representation. An example with a DuoTone connected to port 0
    and FanOut connected to port 4 looks like:

        'H1:SYS-TIMING_C_MA_A:DUOTONE,,,,FANOUT,,,,,,,,,,,'

    Each Timing Slave can have an optional description following the device
    type and separated with a semicolon. Note that this description cannot
    contain the following characters:

        ;:,

    since they are used syntactically within the string. Starting from the
    above example, the FanOut connected to port 4 could be described as "test
    stand":

        'H1:SYS-TIMING_C_MA_A:DUOTONE,,,,FANOUT;test stand,,,,,,,,,,,'

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
    def mfo(self):
        """Return whether the MFO that this string describes is a Master (M) or
        FanOut (F)."""
        return self.split(':')[1].split('_')[2]
    def mfo_id(self):
        """There can be multiple FanOuts in a given location. We distinguish
        between them by assigning letters, starting at A. Return the MFO ID
        letter for the MFO that this string describes.."""
        return self.split(':')[1].split('_')[3]
    def port(self, port_number):
        """There are 16 ports, numbered 0-15, to which Timing Slave modules can
        be connected by fiber link. Return the Timing Slavee connected to a
        particular port. If no device is connected, return None."""
        dev = self.split(':')[2].split(',')[port_number].split(';')
        dev_type = dev[0]
        if dev_type == '':
            return None
        else:
            if len(dev) == 1:
                return TimingSlave(dev_type, self, port_number)
            elif len(dev) == 2:
                return TimingSlave(dev_type, self, port_number,
                                   description=dev[1])
    def portless_name(self):
        """Return a string representing this MFO but with no information about
        used ports. This is not a valid MFO object, but can be used to
        construct valid EPICS channels."""
        return ':'.join(self.split(':')[0:2])
    def mfo_channels(self):
        """Get a list of channels related to this MFO, ignoring any channels
        related to Timing Slave devices attached to this MFO."""
        suffixes = CHANNEL_SUFFIXES['mfo_common']
        for i in range(PORTS_PER_MFO):
            suffixes += ['PORT_' + str(i) + '_' + x for x in
                         CHANNEL_SUFFIXES['mfo_port_related']]
        prefix = self.portless_name() + '_'
        return [prefix + suffix for suffix in suffixes]
    def slave_channels_in_use(self):
        """Get a list of channels in use by this MFO's attached slaves. Does
        not include channels relating to this MFO; returns only Slave-related
        channels."""
        channels = []
        for i in range(PORTS_PER_MFO):
            slave = self.port(i)
            if not slave is None:
                channels += slave.get_channels()
        return channels
    def get_channels_in_use(self):
        """Return a list of all channels in use by this MFO as well as any
        connected Timing Slaves."""
        return self.mfo_channels() + self.slave_channels_in_use()

# if running from the command line, we should run this stuff
def main():
    parser = argparse.ArgumentParser(description=('Query against channel names '
                                     'used by the aLIGO timing system. '
                                     'List all matching channel names.'))
    parser.add_argument('-i','--ifo',
                        help=('Interferometer; "h" is Hanford, "l" is '
                             'Livingston.'))
    parser.add_argument('-s','--subsys',
                        help=('Most timing belongs to "SYS-TIMING", but some '
                             'channels are in other subsystems.'))
    parser.add_argument('-l','--location',
                        help=('Location; "c" is corner station, "x" is X end '
                             'station, "y" is Y end station.'))
    parser.add_argument('-m','--mfo',
                        help=('Is this device connected to a Master or FanOut '
                             'board? "m" specifies a Master, "f" a FanOut.'))
    parser.add_argument('-d','--device_id',
                        help=('"a", "b"... etc. specifies which FanOut (or '
                             'Master) this device connects to (since there '
                             'can be multiple Fanouts at a given location.'))
    parser.add_argument('-p','--port',
                        help=('The port number on the MFO to which this device '
                             'connects; one of {0..15}.'))
    parser.add_argument('-t','--type',
                        help=('The device type. "i" for IRIG-B Module, "x" for '
                             'RFOscillator/oscillator locking, "d" for '
                             'Slave/DuoTone assembly (usually inside an IO '
                             'Chassis), "c" for Timing Comparator Module, or '
                             '"f" for a fanout module.'))
    args = parser.parse_args()
    # TODO: handle parsed arguments
    # TODO: run a query and print results

if __name__ == "__main__":
    main()

