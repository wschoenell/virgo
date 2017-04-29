#!/bin/bash
echo "# SID  specObjID  " `head -n1 /Users/william/data/DR7/tables/sample.FDR7.926246.f.Starlight.SYN0$1.tab.BS | cut -c35-500`
for sid in `awk '{print $1}' join_starlight_specobjid.txt`
do
    echo `grep -m1 ^$sid join_starlight_specobjid.txt` `grep -m1 ^$sid /Users/william/data/DR7/tables/sample.FDR7.926246.f.Starlight.SYN0$1.tab.BS`
done
