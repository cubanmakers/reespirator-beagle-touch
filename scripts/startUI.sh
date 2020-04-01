#!/bin/bash
/usr/bin/X &
/bin/delay 5
export DISPLAY=:0
cd /root/repos/reespirator-beagle-touch/
killall -9 /usr/bin/python3; /usr/bin/nice -n -10 /usr/bin/python3 respyratorctl ui 
