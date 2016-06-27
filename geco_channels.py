#!/usr/bin/env python

# a script/module for querying timing channels.

import argparse

def device_type(end_of_channel_name):
    # TODO: define
    pass

def is_timing(channel_name):
    """Does this channel name follow the timing system naming conventions?"""
    ch_name_array = channel_name.replace(':','_').split('_')
    if ch_name_array[1] == 'SYS-TIMING':
        return True
    else:
        return False

class MFO(object):
    """A master/fanout device."""
    def __init__(self, channel_name):
        # only SYS-TIMING objects are connected to MFOs
        if not is_timing(channel_name):
            raise ValueError("Channel not connected to MFO: "
                             + str(channel_name))
        ch_name_array   = channel_name.upper().replace(':','_').split('_',7)
        self.ifo        = ch_name_array[0]
        self.subsys     = ch_name_array[1]
        self.location   = ch_name_array[2]
        self.mfo        = ch_name_array[3]
        self.device_id  = ch_name_array[4]
        # self.port       = ch_name_array[6]  # [5] is just word "PORT"

    def __repr__(self):
        """Get the partial channel name for this MFO. The __repr__ and __str__
        methods are the same, since string representations of these objects
        are unambiguous.
        """
        return self.ifo + ':' + self.subsys + '_' + self.location +  '_'
            + self.mfo + '_' + self.device_id

    def __str__(self):
        """Get the partial channel name for this MFO. The __repr__ and __str__
        methods are the same, since string representations of these objects
        are unambiguous.
        """
        return __repr__(self)

class Slave(object):
    """A Timing Slave Device."""
    def __init__(self, channel_name):
        # only SYS-TIMING objects can be members.
        if not is_timing(channel_name):
            raise ValueError("Channel not connected to MFO: " 
                             + str(channel_name))
        ch_name_array   = channel_name.upper().replace(':','_').split('_',7)
        self.ifo        = ch_name_array[0]
        self.subsys     = ch_name_array[1]
        self.location   = ch_name_array[2]
        self.mfo        = ch_name_array[3]
        self.device_id  = ch_name_array[4]
        self.port       = ch_name_array[6]  # [5] is just word "PORT"
        self.type       = device_type(ch_name_array[7])

    def __repr__(self):
        """Get the partial channel name for this MFO. The __repr__ and __str__
        methods are the same, since string representations of these objects
        are unambiguous.
        """
        return self.ifo + ':' + self.subsys + '_' + self.location +  '_'
            + self.mfo + '_' + self.device_id + '_PORT_' + self.port + '_'
            + self.type

    def __str__(self):
        """Get the partial channel name for this MFO. The __repr__ and __str__
        methods are the same, since string representations of these objects
        are unambiguous.
        """
        return __repr__(self)

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

