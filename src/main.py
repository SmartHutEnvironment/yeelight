import yeelight;
import paho.mqtt.client as mqtt
import yaml;
import time;
import sys;
import json;
from threading import Event

exit = Event()
import signal
for sig in ('TERM', 'HUP', 'INT'):
    signal.signal(getattr(signal, 'SIG'+sig), quit);


def quit(signo, _frame):
    print("Interrupted by %d, shutting down" % signo)
    exit.set()
    

#TODO: növénymérő

def convert_state(bulb, dest, data, name):
    if not data or data == "off":
        dest[name] = "OFF";
        bulb.last_state = False;
    else:
        dest[name] = "ON";
        bulb.last_state = True;

def convert_number(bulb, dest, data, name):
    dest[name] = int(data);

def convert_raw(bulb, dest, data, name):
    dest[name] = data;

def convert_hex(bulb, dest, data, name):
    dest[name] = "#" + hex(int(data))[2:];

def convert_mode(bulb, dest, data, name):
    if data == yeelight.PowerMode.NORMAL:
        dest[name] = "Normal";
    if data == yeelight.PowerMode.MOONLIGHT:
        dest[name] = "Moonlight";


propertyConverters = {
    "state": convert_state,
    "number": convert_number,
    "raw": convert_raw,
    "hex": convert_hex,
    "lighting_mode": convert_mode,
}

def action_onoff(bulb, data):
    if data == "ON":
        bulb.turn_on();
    if data == "OFF":
        bulb.turn_off();
    if data == "TOGGLE":
        if bulb.last_state == True:
            bulb.turn_off();
        else:
            bulb.turn_on();

def action_mode(bulb, data):
    if data == "Normal":
        bulb.set_power_mode(yeelight.PowerMode.NORMAL);
    if data == "Moonlight":
        bulb.set_power_mode(yeelight.PowerMode.MOONLIGHT);

def action_color(bulb, data):
    bulb.set_rgb(int(data[1:2], 16), int(data[3:4], 16), int(data[5:6], 16));

def action_brightness(bulb, data):
    bulb.set_brightness(int(data));

deviceActions = {
    "turn_on_off": action_onoff,
    "set_brightness": action_brightness,
    "set_mode": action_mode,
    "set_color": action_color,
}

f = open("data/config.yml");
configData = f.read();
f.close();

f = open("data/devices.yml");
deviceData = f.read();
f.close();

config = yaml.load(configData, Loader=yaml.SafeLoader)["yeelight2mqtt"];
deviceConfig = yaml.load(deviceData, Loader=yaml.SafeLoader)["devices"];

class Device:
    def __init__(self, mqtt, device):
        self.bulb = yeelight.Bulb(device["ip"], effect='smooth', duration=device["duration"], power_mode=yeelight.PowerMode.LAST);
        self.mqtt = mqtt;
        self.topic = device["topic"];
        self.report = config["types"][device["type"]]["report"];
        self.actions = config["types"][device["type"]]["actions"];
    
    def ProcessMessage(self, msg):
        for src in self.actions:
            if not src in msg:
                continue;

            action = self.actions[src];
            deviceActions[action](self.bulb, msg[src]);
        pass;
    
    def UpdateStatus(self):
        try:
            props = self.bulb.get_properties();
        except:
            return {"connection": "OFF"};
        
        status = {};

        for src in self.report:
            report = self.report[src];
            try:
                propertyConverters[report["converter"]](self.bulb, status, props[src], report["as"]);
            except:
                print(sys.exc_info()[0]);
                return None;
        
        status["connection"] = "ON";
        return status;


client = mqtt.Client()
devices = {};

for device in deviceConfig:
    devices[device["topic"]+"/set"] = Device(client, device);


def on_connect(client, userdata, flags, rc):
    for topic in devices:
        client.subscribe(topic);

def on_message(client, userdata, msg):
    data = json.loads(msg.payload)
    
    devices[msg.topic].ProcessMessage(data);
    status = devices[msg.topic].UpdateStatus();
    client.publish(devices[msg.topic].topic, json.dumps(status));


client.on_connect = on_connect
client.on_message = on_message

client.connect(config["mqtt"]["host"], 1883, 60)
client.loop_start();
while not exit.is_set():
    for topic in devices:
        status = devices[topic].UpdateStatus();
        client.publish(devices[topic].topic, json.dumps(status));
    exit.wait(config["iteration_gap"]);
