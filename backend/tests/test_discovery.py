import pytest
from backend.app.monitoring.discovery import DiscoveryService


def test_process_discovery():
    processes = DiscoveryService.get_processes(limit=10)
    assert isinstance(processes, list)
    assert len(processes) > 0
    p = processes[0]
    assert "pid" in p
    assert "name" in p
    assert "cpu_percent" in p
    assert "memory_percent" in p


def test_ports_discovery():
    ports = DiscoveryService.get_ports()
    assert isinstance(ports, list)
    if ports:
        port = ports[0]
        assert "protocol" in port
        assert "local_port" in port


def test_services_discovery():
    services = DiscoveryService.get_services()
    assert isinstance(services, list)
    assert len(services) > 0
    s = services[0]
    assert "name" in s
    assert "is_active" in s
