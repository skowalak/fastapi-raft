import logging
from ipaddress import IPv4Address, IPv6Address
from typing import Dict, List

from app.config import Settings
from dns import resolver, reversename

logger: logging.Logger = logging.getLogger(__name__)


def get_hostname_by_ip(address: IPv4Address | IPv6Address) -> str:
    """
    Reverse-lookup an IP-Address to get its corresponding hostname

    Parameters
    ----------
    address : IPv4Address | IPv6Address
        address to be looked up

    Returns
    -------
    str
        hostname if successful
    """
    addr = reversename.from_address(str(address))
    return str(resolver.query(addr, "PTR")[0])


def get_ip_by_hostname(
    hostname: str, record_type: str = "A"
) -> IPv4Address | IPv6Address:
    """
    Resolve DNS record of type `record_type` to ip address.

    Parameters
    ----------
    hostname : str
        fully qualified domain name
    record_type : str, optional
        DNS record type, by default "A"

    Returns
    -------
    IPv4Address | IPv6Address
        ipv4 if type "A", ipv6 if type "AAAA"
    """
    return resolver.query(hostname, record_type)


def discover_by_dns(name: str) -> List[IPv4Address]:
    """
    Use docker builtin DNS capability to find other replicas.

    Parameters
    ----------
    name : str
        app name, which all instances share since they are replicas of each
        other.

    Returns
    -------
    List[IPv4Address]
        list of ip addresses of all replicas.
    """
    return [IPv4Address(ip) for ip in get_ip_by_hostname(name)]


def discover_replicas(settings: Settings) -> Dict[str, str]:
    """
    Discover all replicas of this service in the same Docker network.

    This works by specifying a max_replica parameter (can be passed via
    envvar) and utilizing the [Docker DNS Services][0].

    [0]: https://docs.docker.com/config/containers/container-networking/#dns-services

    Parameters
    ----------
    settings : Settings
        configuration options passed to instance

    Returns
    -------
    Dict[str, str]
        Map domain names of replicas to their IP addresses.
    """
    name = settings.APP_NAME
    ip_addresses = discover_by_dns(name)
    expected, got = settings.NUM_REPLICAS, len(ip_addresses)
    if got != expected:
        logger.error(
            "Number of found replicas does not match configured number: {expected} != {got}."
        )
        raise RuntimeError(
            f"Critical Failure: Expected {expected} replicas, found {got}"
        )
    # remove own address from that
    own_address = discover_by_dns(settings.HOSTNAME)[0]
    replicas = {}
    for address in ip_addresses:
        if not address == own_address:
            fqdn = get_hostname_by_ip(address)
            replicas[fqdn] = address

    logger.debug(f"OWN ADDRESS: {settings.HOSTNAME} :: {own_address}")

    return {k: v for k, v in replicas.items() if v}