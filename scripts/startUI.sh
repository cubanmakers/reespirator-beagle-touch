#!/bin/bash
X &
export DISPLAY=:0
cd 
killall -9 python3; python3 reespirator_ui.py
