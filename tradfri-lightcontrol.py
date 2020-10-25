#!/usr/bin/env python3
#Hack to allow relative import above top level package
#Note: Change /usr/local/lib/python3.6/dist-packages/pytradfri/api/libcoap_api.py line 35 to coap-client full path, example: '/usr/local/bin/coap-client',

import sys
import os
import logging
folder = os.path.dirname(os.path.abspath(__file__))  # noqa
sys.path.insert(0, os.path.normpath("%s/.." % folder))  # noqa

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory
from pytradfri.error import PytradfriError
from pytradfri.util import load_json, save_json

import uuid
import argparse
import threading
import time
#Define Configuration file, use full path to file
CONFIG_FILE = '/home/tradfri/tradfri_standalone_psk.conf'
logging.basicConfig(filename='/var/log/tradfri-cron.log', filemode='a', format='%(asctime)s | %(levelname)s - %(message)s',level=logging.INFO)
#Parse arguments passed to python script
parser = argparse.ArgumentParser()
parser.add_argument('host', metavar='IP', type=str,
                    help='IP Address of your Tradfri gateway')
parser.add_argument('-K', '--key', dest='key', required=False,
                    help='Security code found on your Tradfri gateway')
parser.add_argument('-S', '--state', dest='state', required=True,
                    help='Provide ON/OFF state for lights')
args = parser.parse_args()


if args.host not in load_json(CONFIG_FILE) and args.key is None:
    print("Please provide the 'Security Code' on the back of your "
          "Tradfri gateway:", end=" ")
    key = input().strip()
    if len(key) != 16:
        raise PytradfriError("Invalid 'Security Code' provided.")
    else:
        args.key = key

def observe(api, device):
    def callback(updated_device):
        light = updated_device.light_control.lights[0]
        #print("Received message for: %s" % light)

    def err_callback(err):
        print(err)

    def worker():
        api(device.observe(callback, err_callback, duration=120))

    threading.Thread(target=worker, daemon=True).start()
    #print('Sleeping to start observation task')
    time.sleep(1)

def run():
    # Assign configuration variables.
    # The configuration check takes care they are present.
    conf = load_json(CONFIG_FILE)
    try:
        identity = conf[args.host].get('identity')
        psk = conf[args.host].get('key')
        api_factory = APIFactory(host=args.host, psk_id=identity, psk=psk)
    except KeyError:
        identity = uuid.uuid4().hex
        api_factory = APIFactory(host=args.host, psk_id=identity)

        try:
            psk = api_factory.generate_psk(args.key)
            print('Generated PSK: ', psk)

            conf[args.host] = {'identity': identity,
                               'key': psk}
            save_json(CONFIG_FILE, conf)
        except AttributeError:
            raise PytradfriError("Please provide the 'Security Code' on the "
                                 "back of your Tradfri gateway using the "
                                 "-K flag.")

    api = api_factory.request

    gateway = Gateway()

    devices_command = gateway.get_devices()
    devices_commands = api(devices_command)
    devices = api(devices_commands)

    lights = [dev for dev in devices if dev.has_light_control]

    # Print all lights
    for bulb in lights:
        print(bulb.name)
        observe(api, bulb)
        #print("State: {}".format(bulb.light_control.lights[0].state))
        if args.state == "ON":
            if bulb.light_control.lights[0].state:
                print("The light is already ON")
                logging.warning('Could not turn on light %s, light was already ON' %(bulb.name))
            else:
                print("The light is OFF, turning it ON")
                api(bulb.light_control.set_state(True))
                logging.info('Turning the light %s ON' %(bulb.name))
        elif args.state == "OFF":
            if not(bulb.light_control.lights[0].state):
                print("The light is already OFF")
                logging.warning('Could not turn off light %s, light was already OFF' %(bulb.name))
            else:
                print("The light is ON, turning it OFF")
                api(bulb.light_control.set_state(False))
                logging.info('Turning the light %s OFF' %(bulb.name))

run()
