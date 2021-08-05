from typing import Tuple

from zeroconf import ServiceInfo, Zeroconf

"""
Use this to look up a service when it is not expected to change or be updated.
Usually this would be invoked in a loop polling until there is a response. If
the application needs to react to changes in the service, perhaps it moves
to a different host, then use the listener approach that is in find_services.py
"""


class FindServices():
    zc: Zeroconf

    def __init__(self):
        self.zc = Zeroconf()

    def close(self):
        self.zc.close()

    def get_service_info(self, type: str, name: str) -> ServiceInfo:
        """
        Retrieves the service info matching the given type and name. The name is
        the unqualified service name, e.g. "DYLAN MQTT Server". Makes a query for the
        service and waits a timeout (default 3 seconds) for a response. Returns none
        if the query timesout.
        :param type: The type of the service to be retrieved
        :param name: The name of the service
        :return: The matching service or none if there if the query does not respond
        in less than 3 seconds.
        """
        return self.zc.get_service_info(type_=type, name=f"{name}.{type}")


class ServiceInfoParser():
    # This is the service info
    info: ServiceInfo

    def __init__(self, info: ServiceInfo):
        if info is None:
            raise ValueError("Info parameter must not be None")
        self.info = info

    def get_host_port(self) -> str:
        return f"{self.info.server}:{self.info.port}"

    def get_host_port_tuple(self) -> Tuple[str, int]:
        return self.info.server, self.info.port


def get_service_host_port_block(type: str, name: str, logger) -> Tuple[str, int]:
    """
    Block until the service is available
    :param type: The service type
    :param name: The server name
    :param logger: Feedback messages logged through here, can be None
    :return: A tuple of the hostname (str) and port (int)
    """
    finder = FindServices()
    try:
        while True:
            if logger is not None:
                logger.info("Zeroconf, look up service type (%s) name (%s)", type, name)
            info = finder.get_service_info(type=type, name=name)
            if info is not None:
                hostname, port = ServiceInfoParser(info).get_host_port_tuple()
                break
            else:
                logger.info("Not found, try again")
    except Exception as e:
        logger.error("Unexpected exception %s", str(e))
    finally:
        finder.close()
    return hostname, port
