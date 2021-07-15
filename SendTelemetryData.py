import threading
import json
import requests
import time

from paho.mqtt.publish import single
from requests.auth import HTTPBasicAuth

registryIp = "127.0.0.1"
httpAdapterIp = "127.0.0.1"
mqttAdapterIp = "127.0.0.1"

# example Data
exampleDataList = [
    {"ax": 178.608, "ay": 105.774, "az": 994.544, "gx": 0.63, "gy": -4.62, "gz": -2.1, "hum": 48, "temp": 19,
     "time": 1606380309328},
    {"ax": 177.998, "ay": 104.554, "az": 994.666, "gx": 0.63, "gy": -4.62, "gz": -2.17, "hum": 48, "temp": 19,
     "time": 1606380309145},
    {"ax": 178.852, "ay": 106.506, "az": 994.544, "gx": 0.63, "gy": -4.55, "gz": -2.31, "hum": 48, "temp": 19,
     "time": 1606380308962},
    {"ax": 179.584, "ay": 105.408, "az": 995.032, "gx": 0.63, "gy": -4.55, "gz": -2.38, "hum": 48, "temp": 19,
     "time": 1606380308778},
    {"ax": 176.9, "ay": 108.824, "az": 998.448, "gx": 0.7, "gy": -4.41, "gz": -2.66, "hum": 48, "temp": 19,
     "time": 1606380308598},
    {"ax": 175.802, "ay": 106.14, "az": 993.812, "gx": 0.7, "gy": -4.41, "gz": -2.45, "hum": 48, "temp": 19,
     "time": 1606380308417},
    {"ax": 178.364, "ay": 106.262, "az": 997.96, "gx": 0.63, "gy": -4.55, "gz": -2.38, "hum": 48, "temp": 19,
     "time": 1606380308235}]

def thread_function_Http(tenantId, deviceId, messageCount):
    #send telemtryData
    x = True
    count = 1
    while x:
        for data in exampleDataList:
            print(f"Send {count}. Telemetry Message via HTTP from {deviceId}@{tenantId}")
            response = requests.post(f'http://{httpAdapterIp}:8080/telemetry',
                                    headers={"content-type": "application/json", "hono-ttd": "2"},
                                    data=json.dumps(data),
                                    auth=HTTPBasicAuth(f'{deviceId}@{tenantId}', f'1234'))
            count = count + 1
            if count == messageCount:
                x = False

def thread_function_Mqtt(tenantId, deviceId, messageCount):
    #send telemtryData
    x = True
    count = 1
    while x:
        for data in exampleDataList:
            print(f"Send Telemetry {count}. Message via MQTT from {deviceId}@{tenantId}")
            single("telemetry", payload=json.dumps(data),
                   hostname=mqttAdapterIp,
                   auth={"username": f'{deviceId}@{tenantId}', "password": "1234"})

            time.sleep(2)
            count = count + 1
            if count == messageCount:
                x = False

def sendDataHttp(tenantIds, messageCount=100):
    # print(tenantIds)
    for id in tenantIds:
        # get devices for tenant
        deviceList = getDevicesForTenant(id)

        for device in deviceList:
            x = threading.Thread(target=thread_function_Http, args=(id, device["id"], messageCount))
            x.start()

def sendDataMqtt(tenantIds, messageCount=100):
    for id in tenantIds:
        # get devices for tenant
        deviceList = getDevicesForTenant(id)

        for device in deviceList:
            x = threading.Thread(target=thread_function_Mqtt, args=(id, device["id"], messageCount))
            x.start()

def getDevicesForTenant(tenantId):
    response = requests.get(f'http://{registryIp}:28080/v1/devices/{tenantId}',
                            headers={'content-type': 'application/json'}).json()

    deviceInTenantCount = response["total"]
    deviceList = response["result"]
    return deviceList

def readyForPrinting(tenantId):
    # send http Data to state that the printer is ready to go

    deviceId = getDevicesForTenant(tenantId)[0]["id"]
    count = 1
    x = True
    while x:
        print(f"Send {count}. Telemetry Message via HTTP from Device {tenantId}@{deviceId}")
        response = requests.post(f'http://{httpAdapterIp}:8080/telemetry',
                                 headers={"content-type": "application/json", "hono-ttd": "5"},
                                 data=json.dumps({"Name":f'{tenantId}@{deviceId}', "Status":"Ready To Print!"}),
                                 auth=HTTPBasicAuth(f'{deviceId}@{tenantId}', f'1234'))

        # if receiving a status Code 200, a Command was received.
        if response.status_code == 200:
            # print(response.headers["hono-command"])
            commandRequestId = response.headers["hono-cmd-req-id"]
            commandName = response.headers["hono-command"]
            printingFile = response.json()["PrintingFile"]
            if commandName == "StartPrinting":
                answer = input(f'Start Printing {printingFile} ? (Y/N)')

                if answer == "Y" or answer == "y":
                    print(f'Responding to Command "{commandName}"')
                    commandResponse = requests.put(
                        f'http://{httpAdapterIp}:8080/command/res/{tenantId}/{deviceId}/{commandRequestId}',
                        headers={"content-type": "application/json", "hono-cmd-status": "200"},
                        data=json.dumps({"PrintingStatus": "Printing", "PrintingFile":f'{printingFile}'}),
                        auth=HTTPBasicAuth(f'{deviceId}@{tenantId}', f'1234'))
                    # print(commandResponse.status_code)
                    # print(commandResponse.content)
                    x = False

                    #send event to say that you are starting the printing now
                    SendEvent(tenantId,deviceId,{"Status":"StartedPrinting"})

                    #start sending telemetry data, since you are printing now
                    thread_function_Http(tenantId,deviceId,15)
                    # tx = threading.Thread(target=thread_function_Http, args=(tenantId, deviceId, 20))
                    # tx.start()

                else:
                    print(f'Responding to Command "{commandName}"')
                    commandResponse = requests.put(
                        f'http://{httpAdapterIp}:8080/command/res/{tenantId}/{deviceId}/{commandRequestId}',
                        headers={"content-type": "application/json", "hono-cmd-status": "200"},
                        data=json.dumps({"PrintingStatus": "PrintingFileNotAccepted", "PrintingFile":f'{printingFile}'}),
                        auth=HTTPBasicAuth(f'{deviceId}@{tenantId}', f'1234'))


        if response.status_code != 202 and response.status_code != 200:
            print(response.status_code)
            print(response.content)

        count = count + 1

def SendEvent(tenantId, deviceId, data):
    print(f"Send Event Message via HTTP")
    response = requests.post(f'http://{httpAdapterIp}:8080/event',
                             headers={"content-type": "application/json"},
                             data=json.dumps(data),
                             auth=HTTPBasicAuth(f'{deviceId}@{tenantId}', f'1234'))

    if response.status_code != 202 and response.status_code != 200:
        print(response.status_code)
        print(response.content)