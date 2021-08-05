"""
Uses Python-zeroconf to find services on the local network.
"""
from time import sleep

from zeroconf import ServiceBrowser, Zeroconf, ServiceListener, ServiceInfo

from discovery import FindServices, ServiceInfoParser, get_service_host_port_block


class ZCListener(ServiceListener):

    def remove_service(self, zeroconf, type, name):
        print("Removed service:", zeroconf.get_service_info(type, name))

    def add_service(self, zeroconf, type, name):
        info: ServiceInfo = zeroconf.get_service_info(type, name)
        print("Added service:", "type:", type, "name:", name, "info", info, info.server, info.port)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info: ServiceInfo = zeroconf.get_service_info(type, name)
        print("Updated service:", "type:", type, "name:", name, "info", info, info.server, info.port)


# Demonstrate the query method, make a query to look up the service on demand
service_finder = FindServices()
try:
    type = "_mqtt._tcp.local."
    name = "DYLAN MQTT Server"
    while True:
        info = service_finder.get_service_info(type, name)
        if info is not None:
            break
        else:
            print(f"Service {type} {name} not found, try again in a few seconds")
            sleep(5)
    parser = ServiceInfoParser(info)
    print("info", parser.get_host_port())

    hostname, port = get_service_host_port_block(type=type, name=name)
    print(f"As tuple {hostname}:{port}")
finally:
    service_finder.close()

# The listener approach, a service browser runs a thread in the background
# and informs a listener when there is a change.
try:
    zeroconf = Zeroconf()
    listener = ZCListener()
    browser = ServiceBrowser(zeroconf, "_mqtt._tcp.local.", listener)
    input("Press enter to exit...\n\n")
finally:
    zeroconf.close()
