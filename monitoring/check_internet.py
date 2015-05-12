#!/usr/bin/python

"""
This script runs on the Raspberry PI and checks if it has an internet connection.
If there isn't any, then it restarts.
"""

import subprocess
from time import sleep
import time
import os
hostname = "google.com"

internet_ok = False
attempts = 5
filepath = '/home/pi/Documents/Code/log_internet_down.txt'


def restart():
    command = "/usr/bin/sudo /sbin/shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    
for i in range(0,attempts):
    response = os.system("ping -c 1 " + hostname)
    if response == 0:
        internet_ok = True
        break
    sleep(5)

if not internet_ok:
    datenow = str(time.strftime('%Y-%m-%dT%H:%M:%S+01:00'))
    log_str = datenow + "\n"    
    with open(filepath, 'a') as myFile:
        myFile.write(log_str)
    restart()
