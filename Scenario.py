import sys

import RegisterTenantsAndDevices
import SendTelemetryData

def start():
    x = True
    print("Willkommen")
    while x:
        print()
        print("Wählen sie eine Aktion für die Demo")
        print("---------------------------------------------------------------------")
        print("[1] - Anlegen von Tenants und Devices")
        print("[2] - Senden von telemetrischen Daten durch die registrierten Devices")
        print("[3] - Commands senden")
        print("[4] - Registrierte Tenants anzeigen")
        print("[5] - Registrierte Devices anzeigen")
        print("[6] - Anlegen von Tenants und Devices über Certificate [Todo]")
        print()
        print("[98] - Commands Client")
        print("[99] - Backend Client")
        print()
        print("[-1] - Beenden")
        print("---------------------------------------------------------------------")

        keyinput = input("Aktion: ")

        registeredTenants = []

        try:
            # Anlegen von Tenants und Devices [1]
            if keyinput == "1":
                RegisterTenantsAndDevices.registerTenants()
                input("Enter um zum Menü zu gelangen!")

            # Senden von telemetrischen Daten durch die registrierten Devices [2]
            if keyinput == "2":
                registeredTenants = RegisterTenantsAndDevices.tenant_list
                SendTelemetryData.sendDataHttp(registeredTenants,10)
                SendTelemetryData.sendDataMqtt(registeredTenants,10)
                input("Enter um zum Menü zu gelangen!")

            # Drucker sendet telemetrische Daten um zu zeigen, dass er bereit ist, den Druck per Remote zu starten
            if keyinput == "3":
                registeredTenants = RegisterTenantsAndDevices.tenant_list
                SendTelemetryData.readyForPrinting(registeredTenants[0])
                input("Enter um zum Menü zu gelangen!")

            # registrierte Tenants
            if keyinput == "4":
                registeredTenants = RegisterTenantsAndDevices.tenant_list
                if registeredTenants == []:
                    print("Keine Tenants registriert")
                else:
                    print(registeredTenants)
                input("Enter um zum Menü zu gelangen!")

            # registrierte Devices anzeigen
            if keyinput == "5":
                RegisterTenantsAndDevices.getRegisteredDevices()
                input("Enter um zum Menü zu gelangen!")

            # Tenant und Devices mit Certificates anlegen
            if keyinput == "6":
                # RegisterTenantsAndDevices.getRegisteredDevices()
                input("Enter um zum Menü zu gelangen!")

            # beenden
            if keyinput =="-1":
                x = False

            if keyinput == "99":
                registeredTenants = RegisterTenantsAndDevices.tenant_list
                if registeredTenants == []:
                    print("Keine Tenants registriert")
                else:
                    print("Registrierte Tenants:")
                    print(registeredTenants)
                    tenantId = input("TenantId:")
                    RegisterTenantsAndDevices.getClientCmd(tenantId)
                input("Enter um zum Menü zu gelangen!")

            if keyinput == "98":
                registeredTenants = RegisterTenantsAndDevices.tenant_list
                if registeredTenants == []:
                    print("Keine Tenants registriert")
                else:
                    print("Registrierte Tenants:")
                    print(registeredTenants)
                    tenantId = input("TenantId:")
                    RegisterTenantsAndDevices.getClientCommandsCmd(tenantId)
                input("Enter um zum Menü zu gelangen!")
        except:
            print("Unexpected Error: ", sys.exc_info())
            input("Enter To Close...")
            x = False

