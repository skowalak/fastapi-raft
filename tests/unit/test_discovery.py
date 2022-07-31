from ipaddress import IPv4Address, ip_address
from unittest import mock
import pytest


class TestDNSDiscovery:
    """Test functions related to DNS discovery."""

    @pytest.mark.asyncio
    @mock.patch("dns.reversename.from_address")
    @mock.patch("dns.resolver.resolve", return_value=["myname.tld"])
    async def test_reverse_lookup(
        self, mock_resolve: mock.Mock, mock_from_address: mock.Mock
    ):
        # setup
        address = "10.0.0.1"
        expected = "myname.tld"

        # execution
        from app.raft.discovery import get_hostname_by_ip

        got = get_hostname_by_ip(address)

        # test
        assert got == expected
        mock_resolve.assert_called_once()
        mock_from_address.assert_called_once_with("10.0.0.1")

    @pytest.mark.asyncio
    @mock.patch("dns.resolver.resolve", return_value="10.0.0.1")
    async def test_hostname_ipv4_lookup(self, mock_resolve: mock.Mock):
        # setup
        hostname = "myname.tld"
        expected = "10.0.0.1"

        # execution
        from app.raft.discovery import get_ip_by_hostname

        got = get_ip_by_hostname(hostname, "A")

        # test
        assert got == expected
        mock_resolve.assert_called_once_with(hostname, "A")

    @pytest.mark.asyncio
    @mock.patch(
        "app.raft.discovery.get_ip_by_hostname",
        return_value=[ip_address("10.0.0.1"), ip_address("10.0.0.2")],
    )
    async def test_multiple_hostname_lookup(self, mock_get_ip: mock.Mock):
        # setup
        name = "myname.tld"
        expected = [ip_address("10.0.0.1"), ip_address("10.0.0.2")]

        # execution
        from app.raft.discovery import discover_by_dns

        got = discover_by_dns(name)

        # test
        assert got == expected
        mock_get_ip.assert_called_once_with(name)

    @pytest.mark.asyncio
    @mock.patch("app.raft.discovery.discover_by_dns")
    @mock.patch(
        "app.raft.discovery.get_hostname_by_ip", return_value="myname-replica1.tld"
    )
    async def test_multiple_hostname_lookup(
        self, mock_get_hostname: mock.Mock, mock_discover: mock.Mock
    ):
        # setup
        hostname = "myname.tld"
        expected = "myname-replica1.tld"

        # execution
        from app.raft.discovery import get_replica_name_by_hostname

        got = get_replica_name_by_hostname(hostname)

        # test
        assert got == expected

    def dns_lookup_side_effect(ip: str):
        map = {
            "10.0.0.2": "myname-replica1.tld",
            "10.0.0.3": "myname-replica2.tld",
            "10.0.0.4": "myname-replica3.tld",
        }
        return map.get(ip, None)

    @pytest.mark.asyncio
    @mock.patch(
        "app.raft.discovery.discover_by_dns",
        return_value=["10.0.0.2", "10.0.0.3", "10.0.0.4"],
    )
    @mock.patch(
        "app.raft.discovery.get_hostname_by_ip", side_effect=dns_lookup_side_effect
    )
    @mock.patch("app.raft.discovery.get_ip_by_hostname", return_value=["10.0.0.2"])
    async def test_full_replica_discovery(
        self,
        mock_get_ip: mock.Mock,
        mock_get_hostname: mock.Mock,
        mock_discover: mock.Mock,
    ):
        # setup
        app_name = "myname.tld"
        hostname = "myname-replica1.tld"
        expected = {
            "myname-replica2.tld": "10.0.0.3",
            "myname-replica3.tld": "10.0.0.4",
        }

        # execution
        from app.raft.discovery import discover_replicas

        got = discover_replicas(app_name, hostname)

        # test
        assert got == expected
        mock_get_ip.assert_called_once_with(hostname)
        mock_get_hostname.assert_called()
        mock_discover.assert_called_once_with(app_name)
