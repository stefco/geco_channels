#!/bin/sh

# first argument is filename. do sed in-place replacement of channel names with
# URLs linking to LIGODV searches for that channel name.

sed -i.orig 's|l.dv/\([a-zA-Z0-9_-]*\):\([a-zA-Z0-9_-]*\)|https\://ldvw.ligo.caltech.edu/ldvw/view?act=baseChan\&amp;baseSelector=true\&amp;ifo=any\&amp;subsys=any\&amp;fsCmp=%3E%3D\&amp;fs=any\&amp;chnamefilt=\1%3A\2\&amp;currentOnly=show+only+currently+acquired\&amp;submitAct=Retrieve+Channel+List+%BB|g' "$1"
