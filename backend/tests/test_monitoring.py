import pytest
from backend.app.monitoring.linux_collector import LinuxCollector


def test_cpu_info():
    cpu = LinuxCollector.get_cpu_info()
    assert "cpu_percent" in cpu
    assert "cpu_count" in cpu
    assert cpu["cpu_count"] >= 1
    assert isinstance(cpu["per_cpu_percent"], list)


def test_memory_info():
    mem = LinuxCollector.get_memory_info()
    assert "ram_total" in mem
    assert "ram_used" in mem
    assert "ram_available" in mem
    assert "ram_percent" in mem
    assert mem["ram_total"] > 0
    assert 0 <= mem["ram_percent"] <= 100


def test_disk_info():
    disk = LinuxCollector.get_disk_info()
    assert "disk_total" in disk
    assert "disk_free" in disk
    assert "disk_percent" in disk
    assert disk["disk_total"] > 0


def test_system_summary():
    sys_sum = LinuxCollector.get_system_summary()
    assert "hostname" in sys_sum
    assert "uptime_seconds" in sys_sum
    assert sys_sum["uptime_seconds"] >= 0


def test_collect_full_metrics():
    metrics = LinuxCollector.collect_full_metrics()
    assert "cpu_percent" in metrics
    assert "ram_percent" in metrics
    assert "status" in metrics
    assert metrics["status"] in ["healthy", "warning", "critical"]
