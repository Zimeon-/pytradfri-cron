#!/usr/bin/env python3
import sys
import os
import urllib.request, requests, json
import datetime, time
import argparse
from datetime import timedelta
from tzlocal import get_localzone # $ pip install tzlocal
import logging
from pytradfri.util import load_json
import pip
from pip.req import parse_requirements
import pkg_resources
from pkg_resources import DistributionNotFound, VersionConflict

#Parse arguments passed to python script
parser = argparse.ArgumentParser()
parser.add_argument('-c','--civil', action='store_true', dest='civil', default=False,
                    help='Use Civil Twilight, Dawn, and Dusk')
parser.add_argument('-n','--nautical', action='store_true', dest='nautical', default=False,
                    help='Use Nautical Twilight, Dawn, and Dusk')
parser.add_argument('--deltahours', dest="deltahours", type=int,
                    default=0, help='Timedelta in hours (Default: 0)')
parser.add_argument('--deltaminutes', dest="deltaminutes", type=int,
                    default=0, help='Timedelta in minutes (Default: 0)')
args = parser.parse_args()

# Define logging file location and format
logging.basicConfig(filename='/var/log/tradfri-cron.log', filemode='a', format='%(asctime)s | %(levelname)s - %(message)s',level=logging.DEBUG)
# Define Configuration file, use full path to file
CONFIG_FILE = '/home/tradfri/tradfri_standalone_psk.conf'

def check_dependencies():
    """
    Checks to see if the python dependencies are fullfilled.
    If check passes return 0. Otherwise print error and return 1
    """
    # dependencies can be any iterable with strings,
    # e.g. file line-by-line iterator
    dependencies = [
        'tzlocal>=0.6.1'
    ]
    session = pip.download.PipSession()
    try:
        pkg_resources.working_set.require(dependencies)
    except VersionConflict as e:
        try:
            print("{} was found on your system, "
                  "but {} is required.\n".format(e.dist, e.req))
            return 1
        except AttributeError:
            print(e)
            return 1
    except DistributionNotFound as e:
        print(e)
        return 1
    return 0

check_dependencies()

if os.path.isfile(CONFIG_FILE):
    logging.info(
        'Configuration file %s found' %(CONFIG_FILE))
else:
    logging.warning('Pytradfri configuration file %s not found!' %(CONFIG_FILE))
    while True:
        try:
            CONFIG_FILE = input("Enter pytradfri configuration location: ")
            if os.path.isfile(CONFIG_FILE):
                print("File %s found" %(CONFIG_FILE))
                break
        except err:
            logging.warning('Pytradfri configuration file %s not found!' %(CONFIG_FILE))

# Assign configuration variables.
# The configuration check takes care they are present.
# Select first conf key as the host (Assuming we only have one)
conf = load_json(CONFIG_FILE)
host = list(conf)[0]
#Get current
data = urllib.request.urlopen("https://api.sunrise-sunset.org/json?lat=60.454510&lng=22.264824&formatted=0").read()
json = json.loads(data)
if args.nautical:
    sunset = datetime.datetime.strptime(json["results"]["nautical_twilight_end"][:-6]+'+0000', '%Y-%m-%dT%H:%M:%S%z').astimezone(get_localzone())
elif args.civil:
    sunset = datetime.datetime.strptime(json["results"]["civil_twilight_end"][:-6]+'+0000', '%Y-%m-%dT%H:%M:%S%z').astimezone(get_localzone())
else:
    sunset = datetime.datetime.strptime(json["results"]["sunset"][:-6]+'+0000', '%Y-%m-%dT%H:%M:%S%z').astimezone(get_localzone())

if args.nautical:
    sunrise = datetime.datetime.strptime(json["results"]["nautical_twilight_begin"][:-6]+'+0000', '%Y-%m-%dT%H:%M:%S%z').astimezone(get_localzone())
elif args.civil:
    sunrise = datetime.datetime.strptime(json["results"]["civil_twilight_begin"][:-6]+'+0000', '%Y-%m-%dT%H:%M:%S%z').astimezone(get_localzone())
else:
    sunrise = datetime.datetime.strptime(json["results"]["sunrise"][:-6]+'+0000', '%Y-%m-%dT%H:%M:%S%z').astimezone(get_localzone())

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
sunsetdelta = sunset + timedelta(hours=args.deltahours,minutes=args.deltaminutes)
logging.info('Updating sunset %s:%s time, real sunset at %s:%s' %(sunsetdelta.hour,sunsetdelta.minute,sunset.hour,sunset.minute))
data = "%s %s * * * root /usr/bin/python3 /home/tradfri/tradfri-lightcontrol.py %s -S ON\n" %(sunsetdelta.minute,sunsetdelta.hour,host)
f.write(data)
# Turn off lights one hour early
sunrisedelta = sunrise - timedelta(hours=args.deltahours,minutes=args.deltaminutes)
logging.info('Updating sunrise %s:%s, real sunrise at %s:%s' %(sunrisedelta.hour,sunrisedelta.minute,sunrise.hour,sunrise.minute))
data = "%s %s * * * root /usr/bin/python3 /home/tradfri/tradfri-lightcontrol.py %s -S OFF\n" %(sunrisedelta.minute,sunrisedelta.hour,host)
f.write(data)
# Close file handler
f.close()
