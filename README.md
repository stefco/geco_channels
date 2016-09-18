# GECo Channels

Utilities for organizing and querying LIGO timing-related channels.

## `geco_channels.py`

A script for storing data about the timing system's current configuration
with plenty of command line options (and a simple internal python interface)
for filtering the channel list.

## Site Maps

There are two as-installed site maps saved in Omnigraffle format. You will need
Omnigraffle (and hence a Mac) to open them. When exported to PDF, each timing
device is clickable and will link to a page on LIGO DV Web with a list of
relevant channels for that device, from which point you can make plots in your
browser using LIGO DV Web, or just use the channel names you have found.
The names of devices in the map can also be directly used to reconstruct
at least partial channel name information.

Channel names, as used in `dataviewer` and `sitemap`, can be constructed by
concatenating the italicized names with an underscore between them, starting
with the nearest Master/Fanout. For example, the below comparator (the yellow
device) would have channel names beginning with:
`L1:SYS-TIMING_Y_FO_A_PORT_9_SLAVE_CFC`

![Timing Comparator](/data/example-device.png)

While onsite, use the `sitemap` command from any terminal to view a menu of
MEDM control screens. Click SYS > Timing to get a "green screen" real time view
of the timing system.

Use `dataviewer` from any terminal to get timeseries data on any of these
channels. Go to the Signal tab, select the Slow checkbox in the bottom left
corner, and navigate through `L1` > `L1:SYS` > `L1:SYS-TIMING` and so on until
you’ve found the relevant channel. All possible channels are listed, regardless
of whether they are in active use.

Timing devices connect to the ports on the front of a master/fanout module via
a fiber connection. There are 16 ports on any given master/fanout. Keep the
timing map up-to-date by placing devices beside the master/fanout ports to
which they are connected.

### Updating the Site Maps

1.  When editing this map in Omnigraffle, make sure to add a URL action in the
    "Properties" section of the "Inspect" sidebar. For the URL, write the prefix
    l.dv/ (which will later be expanded to a list of channel name results on
    LIGO-DV-Web) followed by the partial channel name (should look like
    l.dv/<channel-name>)
2.  Run the `add_ligo_dv_links.sh` script (full text below), which should also
    be contained in this repository on this graffle file. For example, if the
    SVG file is called map.svg, you would run `./add_ligo_dv_links.sh map.svg.`
3.  Re-open this file and confirm that any new links have been expanded
    properly.
4.  Export to your preferred format. SVG, PDF, and HTML all preserve links;
    other image formats do no.

#### Full text of `add_ligo_dv_links.sh`

_(note that the sed command is a single line)_

```bash
#!/bin/sh

sed -i.orig 's|l.dv/\([a-zA-Z0-9_-]*\):\([a-zA-Z0-9_-]*\)|https\://ldvw.ligo.caltech.edu/ldvw/view?act=baseChan\&amp;baseSelector=true\&amp;ifo=any\&amp;subsys=any\&amp;fsCmp=%3E%3D\&amp;fs=any\&amp;chnamefilt=\1%3A\2\&amp;currentOnly=show+only+currently+acquired\&amp;submitAct=Retrieve+Channel+List+%BB|g' "$1"
```
