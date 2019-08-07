# pytradfri-cron

Based on pytradfri library to create cron updates for Ikea Trådfri lights. 

A lot can be updated, this is the first working copy. This is not intended to work out of the box, please read this readme and change settings accordingly!

Requirements:
1. https://www.crummy.com/software/BeautifulSoup/bs4/doc/ (apt install python3-bs4)
2. https://github.com/ggravlingen/pytradfri (pip3 install pytradfri[async])

How to use:

1. Download and test pytradfri by ggravlingen here: https://github.com/ggravlingen/pytradfri
2. Download tradfri-lightcontrol.py and tradfri-updatesun.py
3. Change sunsire and sunset source URL
4. One hour timedelta hard coded as of now
5. Change tradfri-lightcontrol.py to only control lights you want to (All lights in example)
6. Change config file location

Note: Change /usr/local/lib/python3.6/dist-packages/pytradfri/api/libcoap_api.py line 35 to coap-client full path, example: '/usr/local/bin/coap-client'
