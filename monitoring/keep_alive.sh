#!/bin/bash

# This script checks every minute if the intended process is currently running. 
# If it is not, then it restarts it.

while true; do
  ps --no-headers -C read_stick_post.py || /home/pi/Documents/Code/./read_stick_post.py
  sleep 1m
done
