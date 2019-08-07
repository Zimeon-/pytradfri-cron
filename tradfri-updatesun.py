#!/usr/bin/env python3
import sys
import os
from typing import Dict, Any

import requests
import datetime
import argparse
import time
from datetime import timedelta
import logging
from pytradfri.util import load_json
from bs4 import BeautifulSoup as BS

#Define Configuration file, use full path to file
CONFIG_FILE = '/home/tradfri/tradfri_standalone_psk.conf'
logging.basicConfig(filename='/var/log/tradfri-cron.log', filemode='a', format='%(asctime)s | %(levelname)s - %(message)s',level=logging.DEBUG)

#Parse arguments passed to python script
parser = argparse.ArgumentParser()
parser.add_argument('--deltahours', dest="deltahours", type=int,
                    default=1, help='Timedelta in hours (Default: 1)')
parser.add_argument('--deltaminutes', dest="deltaminutes", type=int,
                    default=0, help='Timedelta in minutes (Default: 0)')
args = parser.parse_args()

# Assign configuration variables.
# The configuration check takes care they are present.
# Select first conf key as the host (Assuming we only have one)
conf = load_json(CONFIG_FILE)
host = list(conf)[0]

# Request sunrise and sunset source webpage
r = requests.get('https://ilmatieteenlaitos.fi/saa/Turku', verify=True)
soup = BS(r.text, "html.parser")
# Use Beutiful Soup to get Sunrise and Sunset values, split with : to get hour and minute
sunrise: Dict[str, int] = {"hour": list(map(int,((soup.find('span', {"class": "sunrise"}).text).split(":"))))[0],
           "minute": list(map(int,((soup.find('span', {"class": "sunrise"}).text).split(":"))))[1]}
sunset: Dict[str, int]  = {"hour": list(map(int,((soup.find('span', {"class": "sunset"}).text).split(":"))))[0],
          "minute": list(map(int,((soup.find('span', {"class": "sunset"}).text).split(":"))))[1]}

# Clear current crond config
open("/etc/cron.d/tradfri-lightcontrol", 'w').close()
#* * * * * *
#| | | | | |
#| | | | | +-- Year              (range: 1900-3000)
#| | | | +---- Day of the Week   (range: 1-7, 1 standing for Monday)
#| | | +------ Month of the Year (range: 1-12)
#| | +-------- Day of the Month  (range: 1-31)
#| +---------- Hour              (range: 0-23)
#+------------ Minute            (range: 0-59)

# Open cron for writing new configuration
f = open("/etc/cron.d/tradfri-lightcontrol", "a")
logging.info('Timedelta %d hours and %d minutes' %(args.deltahours,args.deltaminutes))
# Turn on lights with one hour delay
date = datetime.datetime.now().replace(hour=sunset['hour'], minute=sunset['minute']) + timedelta(hours=args.deltahours,minutes=args.deltaminutes)
logging.info('Updating sunset %s:%s time, real sunset at %s:%s' %(date.hour,date.minute,sunset['hour'],sunset['minute']))
data = "%s %s * * * root /usr/bin/python3 /home/tradfri/tradfri-lightcontrol.py %s -S ON\n" %(date.minute,date.hour,host)
f.write(data)
# Turn off lights one hour early
date = datetime.datetime.now().replace(hour=sunrise['hour'], minute=sunrise['minute']) - timedelta(hours=args.deltahours,minutes=args.deltaminutes)
logging.info('Updating sunrise %s:%s, real sunrise at %s:%s' %(date.hour,date.minute,sunrise['hour'],sunrise['minute']))
data = "%s %s * * * root /usr/bin/python3 /home/tradfri/tradfri-lightcontrol.py %s -S OFF\n" %(date.minute,date.hour,host)
f.write(data)
# Close file handler
f.close()
