from __future__ import print_function, unicode_literals

import json
import threading
import time

import requests
from paho.mqtt.publish import single
from requests.auth import HTTPBasicAuth

registryIp = "127.0.0.1"
httpAdapterIp = "127.0.0.1"
mqttAdapterIp = "127.0.0.1"
amqpNetworkIp = "127.0.0.1"
kafkaIp = "127.0.0.1"
pathToPackages = f'C:/Users/Marvin Gossen/Neuer Ordner/packages-master'

tenant_list = []

def registerTenants():
    register_tenant = "Y"
    while register_tenant == "Y":
        tenant_name = input("Geben Sie einen Namen für einen Tenant ein:")

        # Delete existing tenant and devices

        # check for existing Tenant
        response = requests.get(f'http://{registryIp}:28080/v1/tenants/{tenant_name}')

        if response.status_code == 200:

            # check for existing devices in Tenant and delete them
            response = requests.get(f'http://{registryIp}:28080/v1/devices/{tenant_name}',
                                    headers={'content-type': 'application/json'})
            if response.status_code == 200:
                registeredDevices = response.json()["result"]
                for device in registeredDevices:
                    requests.delete(f'http://{registryIp}:28080/v1/devices/{tenant_name}/{device["id"]}')

            # delete Tenant
            response = requests.delete(f'http://{registryIp}:28080/v1/tenants/{tenant_name}')

        # Register Tenant
        tenant = requests.post(f'http://{registryIp}:28080/v1/tenants/{tenant_name}').json()
        tenantId = tenant["id"]
        if tenantId not in tenant_list:
            tenant_list.append(tenantId)

        print(f'Registered tenant {tenantId}')

        device_count = input(f'Wie viele Devices wollen sie für den Tenant {tenant_name} registrieren?')

        print(f'{device_count} wird/werden für {tenant_name} registriert')

        count = 1
        while count <= int(device_count):
            # Add Device to Tenant
            device = requests.post(f'http://{registryIp}:28080/v1/devices/{tenantId}/3D-Printer-{count}').json()
            deviceId = device["id"]

            print(f'Registered device {deviceId}')
            count = count + 1

            # Set Device Password
            devicePassword = "1234"
            code = requests.put(f'http://{registryIp}:28080/v1/credentials/{tenantId}/{deviceId}',
                                headers={'content-type': 'application/json'},
                                data=json.dumps(
                                    [{"type": "hashed-password", "auth-id": deviceId,
                                      "secrets": [{"pwd-plain": devicePassword}]}]))

            if code.status_code == 204:
                print("Password is set!")
            else:
                print("Unnable to set Password")

        register_tenant = input("Ein weiteren Tenant anlegen? (Y)/(N)").upper()

    print()
    print("########################################################")
    print()
    # get Tenant and Devices
    getRegisteredDevices()

def getRegisteredDevices():
    print("Folgende Tenants mit folgenden Devices sind registriert:")
    print()
    if tenant_list == []:
        print("Keine Tenants vorhanden!")

    for tenant_id in tenant_list:
        response = requests.get(f'http://{registryIp}:28080/v1/devices/{tenant_id}',
                                headers={'content-type': 'application/json'}).json()

        deviceInTenantCount = response["total"]
        deviceList = response["result"]
        print(f'Für den Tenant "{tenant_id}" sind insgesamt {deviceInTenantCount} Devices registriert')
        for device in deviceList:
            print(device["id"])
        print()

def getClientCmd(tenantId):
    cmd = f'java -jar hono-cli-1.8.1-exec.jar --hono.client.host={amqpNetworkIp} ' \
            f'--hono.client.port=15672 --hono.client.username=consumer@HONO ' \
            f'--hono.client.password=verysecret --spring.profiles.active=receiver ' \
            f'--tenant.id={tenantId}'
    print(cmd)

def getClientCommandsCmd(tenantId):
    cmd = f'java -jar hono-cli-1.8.1-exec.jar' \
          f' --hono.client.host=127.0.0.1 --hono.client.port=15672' \
          f' --hono.client.username=consumer@HONO --hono.client.password=verysecret ' \
          f'--spring.profiles.active=command ' \
          f'--tenant.id={tenantId} --device.id=3D-Printer-1'
    print(cmd)

