import json
import paho.mqtt.client as mqtt
import requests
from zeroconf import ServiceBrowser, Zeroconf
import socket

class MyListener:
    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        print("Service %s added, service info: %s" % (name, info))

with open('config.json') as config_file:
    config = json.load(config_file)

client = mqtt.Client(config['mqtt']['client_id'], transport='websockets')
client.username_pw_set(config['mqtt']['username'], config['mqtt']['password'])

try:
    client.connect(config['mqtt']['server'], config['mqtt']['port'])
except:
    print("Bitte überprüfen sie die richtigkeit des MQTT Clients! MQTT Client muss gestartet sein. Benutzername und Passwort überprüfen!")

for inverter_config in config['inverters']:
    if inverter_config['auto_discover']:
        zeroconf = Zeroconf()
        listener = MyListener()
        browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
        info = zeroconf.get_service_info("_http._tcp.local.", inverter_config['inverterName'])
        if info:
            IPadressInverter = socket.inet_ntoa(info.address)
        zeroconf.close()
    else:
        IPadressInverter = inverter_config['ip_address']

    InverterPort = inverter_config['port']
    URLInverter = "http://" + IPadressInverter + ":"+InverterPort+"/"

    def testStatusID():
        responseStatusInverter = requests.get(URLInverter + "getOnOff")
        if responseStatusInverter.status_code == 200:
            status = responseStatusInverter.json()
            if status == 0:
                data = getData()
                sendData(data)

    def getData():
        responseDataInverter = requests.get(URLInverter + "getOutputData")
        if responseDataInverter.status_code == 200:
            return responseDataInverter.json()
        else:
            print("Fehler beim Abrufen der Daten vom Wechselrichter.")
            return None

    def sendData(inverterOutput):
        if inverterOutput is not None:
            mqttData = inverterOutput
            client.publish(config['mqtt']['topic'], json.dumps(mqttData))
        else:
            print("Keine Daten zum Senden vorhanden.")
            
    testStatusID()