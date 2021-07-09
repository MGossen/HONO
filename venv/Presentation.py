from __future__ import print_function, unicode_literals

import json
import threading
import time

import requests
from paho.mqtt.publish import single
from requests.auth import HTTPBasicAuth


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

registryIp = "127.0.0.1"
httpAdapterIp = "127.0.0.1"
mqttAdapterIp = "127.0.0.1"
amqpNetworkIp = "127.0.0.1"
kafkaIp = "127.0.0.1"
pathToPackages = f'C:/Users/Marvin Gossen/Neuer Ordner/packages-master'

use_kafka = True

# Delete existing tenant and device
deleteResponse = requests.delete(f'http://{registryIp}:28080/v1/devices/IHBR/3D-Printer-1')
requests.delete(f'http://{registryIp}:28080/v1/tenants/IHBR')

# Register Tenant
tenant = requests.post(f'http://{registryIp}:28080/v1/tenants/IHBR').json()
tenantId = tenant["id"]

print(f'Registered tenant {tenantId}')

# Add Device to Tenant
device = requests.post(f'http://{registryIp}:28080/v1/devices/{tenantId}/3D-Printer-1').json()
deviceId = device["id"]

print(f'Registered device {deviceId}')

# Set Device Password
devicePassword = "my-printer-password"
code = requests.put(f'http://{registryIp}:28080/v1/credentials/{tenantId}/{deviceId}',
                    headers={'content-type': 'application/json'},
                    data=json.dumps(
                        [{"type": "hashed-password", "auth-id": deviceId, "secrets": [{"pwd-plain": devicePassword}]}]))

if code.status_code == 204:
    print("Password is set!")
else:
    print("Unnable to set Password")

# Now we can start the client application
print("We could use the Hono Client now...")
print()
if use_kafka == True:

    print(pathToPackages)
    cmd = f'java -jar hono-cli-1.8.0-exec.jar --tenant.id={tenantId}' \
          f' --spring.profiles.active=receiver,kafka --hono.kafka.commonClientConfig.bootstrap.servers={kafkaIp}:9094' \
          f' --hono.kafka.commonClientConfig.security.protocol=SASL_SSL' \
          f' --hono.kafka.commonClientConfig.sasl.mechanism=SCRAM-SHA-512' \
          f' --hono.kafka.commonClientConfig.sasl.jaas.config="org.apache.kafka.common.security.scram.ScramLoginModule required username=\"hono\" password=\"hono-secret\";"' \
          f' --hono.kafka.commonClientConfig.ssl.endpoint.identification.algorithm=""' \
          f' --hono.kafka.commonClientConfig.ssl.truststore.location="{pathToPackages}/charts/hono/example/certs/trustStore.jks"' \
          f' --hono.kafka.commonClientConfig.ssl.truststore.password=honotrust'
else:
    cmd = f'java -jar hono-cli-1.8.0-exec.jar --hono.client.host={amqpNetworkIp} ' \
        f'--hono.client.port=15672 --hono.client.username=consumer@HONO ' \
        f'--hono.client.password=verysecret --spring.profiles.active=receiver ' \
        f'--tenant.id={tenantId}'
print(cmd)
print()

input("Press Enter to continue...")


def sendingEvents():
    # try sending event via Http
    print(f"Send Event Message via HTTP")
    response = requests.post(f'http://{httpAdapterIp}:8080/event',
                             headers={"content-type": "application/json"},
                             data=json.dumps({"alarm": "FIRE"}),
                             auth=HTTPBasicAuth(f'{deviceId}@{tenantId}', f'{devicePassword}'))

    if response.status_code != 202 and response.status_code != 200:
        print(response.status_code)
        print(response.content)

    # try sending event via MQTT
    print(f"Send Event Message via MQTT")
    single(topic=f"event", qos=1, payload=json.dumps({"alarm": "FIRE"}),
                hostname=mqttAdapterIp,
                auth={"username": f'{deviceId}@{tenantId}', "password": devicePassword})

    time.sleep(2)


def sendingTelemetry():
    count = 1
    # Send HTTP Message
    x = False
    while x:
        for data in exampleDataList:
            print(f"Send {count}. Telemetry Message via HTTP")
            response = requests.post(f'http://{httpAdapterIp}:8080/telemetry',
                                     headers={"content-type": "application/json", "hono-ttd": "2"},
                                     data=json.dumps(data),
                                     auth=HTTPBasicAuth(f'{deviceId}@{tenantId}', f'{devicePassword}'))

            # if receiving a status Code 200, a Command was received.
            if response.status_code == 200:
                print(response.content)
                commandRequestId = response.headers["hono-cmd-req-id"]
                print(f"Responding to Command")
                commandResponse = requests.put(
                    f'http://{httpAdapterIp}:8080/command/res/{tenantId}/{deviceId}/{commandRequestId}',
                    headers={"content-type": "application/json", "hono-cmd-status": "200"},
                    data=json.dumps({"PrintingInProgress": "Canceled"}),
                    auth=HTTPBasicAuth(f'{deviceId}@{tenantId}', f'{devicePassword}'))
                print(commandResponse.status_code)
                print(commandResponse.content)

            if response.status_code != 202 and response.status_code != 200:
                print(response.status_code)
                print(response.content)

            count = count + 1
            if count == 1000:
                x = False

    input("Ready to send Data via MQTT. Press Enter...")

    count = 1
    # Send Message via MQTT
    while not x:
        for data in exampleDataList:
            print(f"Send Telemetry {count}. Message via MQTT")
            single("telemetry", payload=json.dumps(data),
                   hostname=mqttAdapterIp,
                   auth={"username": f'{deviceId}@{tenantId}', "password": devicePassword})

            time.sleep(2)
            count = count + 1

    # Wait a bit for the MQTT Message to arrive
    time.sleep(1)


sendingEvents()

# sendingTelemetry()
