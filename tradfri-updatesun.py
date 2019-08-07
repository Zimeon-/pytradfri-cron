#!/usr/bin/env python3
import requests
import datetime
from datetime import timedelta
import logging
from bs4 import BeautifulSoup as BS

logging.basicConfig(filename='/var/log/tradfri-cron.log', filemode='a', format='%(asctime)s | %(levelname)s - %(message)s',level=logging.DEBUG)

r = requests.get('https://ilmatieteenlaitos.fi/saa/Turku', verify=True)
soup = BS(r.text, "html.parser")
#Use Beutiful Soup to get Sunrise and Sunset values, split with : to get hour and minute
sunrise = {}
sunrise['hour'],sunrise['minute'] = map(int,((soup.find('span',{"class":"sunrise"}).text).split(":")))
sunset = {}
sunset['hour'],sunset['minute'] = map(int,((soup.find('span',{"class":"sunset"}).text).split(":")))

#Clear current crond config
open("/etc/cron.d/tradfri-ulkovalot", 'w').close()
#* * * * * *
#| | | | | |
#| | | | | +-- Year              (range: 1900-3000)
#| | | | +---- Day of the Week   (range: 1-7, 1 standing for Monday)
#| | | +------ Month of the Year (range: 1-12)
#| | +-------- Day of the Month  (range: 1-31)
#| +---------- Hour              (range: 0-23)
#+------------ Minute            (range: 0-59)

#Open cron for writing new configuration
f = open("/etc/cron.d/tradfri-ulkovalot", "a")
#Turn on lights with one hour delay
date = datetime.datetime.now().replace(hour=sunset['hour'], minute=sunset['minute']) + timedelta(hours=1)
logging.info('Updating sunset %s:%s time, real sunset at %s:%s' %(date.hour,date.minute,sunset['hour'],sunset['minute']))
data = "%s %s * * * root /usr/bin/python3 /home/tradfri/tradfri-ulkovalot.py 172.17.0.179 -S ON\n" %(date.minute,date.hour)
f.write(data)
#Turn off lights one hour early
date = datetime.datetime.now().replace(hour=sunrise['hour'], minute=sunrise['minute']) - timedelta(hours=1)
logging.info('Updating sunrise %s:%s, real sunrise at %s:%s' %(date.hour,date.minute,sunrise['hour'],sunrise['minute']))
data = "%s %s * * * root /usr/bin/python3 /home/tradfri/tradfri-ulkovalot.py 172.17.0.179 -S OFF\n" %(date.minute,date.hour)
f.write(data)
#Close file handler
f.close()
