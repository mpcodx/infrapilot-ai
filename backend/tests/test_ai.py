import pytest
from backend.app.ai.ollama_service import OllamaService


@pytest.mark.asyncio
async def test_ollama_health():
    service = OllamaService()
    health = await service.check_health()
    assert "available" in health
    if health["available"]:
        assert isinstance(health["models"], list)
        assert health["model_present"] is True


@pytest.mark.asyncio
async def test_ollama_fallback():
    # Service pointing to an invalid port to test deterministic fallback
    offline_service = OllamaService(base_url="http://127.0.0.1:99999")
    res = await offline_service.generate_response(
        query="What is the CPU status?",
        context={"metrics": {"cpu_percent": 88.5, "ram_percent": 45.0, "disk_percent": 50.0}}
    )
    assert res["is_fallback"] is True
    assert res["model"] == "rule-based-fallback"
    assert len(res["suggested_commands"]) > 0
    assert "top" in res["suggested_commands"][0] or "free" in res["suggested_commands"][0]


@pytest.mark.asyncio
async def test_ollama_prompt_sanitization():
    service = OllamaService()
    res = service._sanitize("hello\x00\x1fworld; rm -rf /")
    assert "\x00" not in res
    assert "\x1f" not in res
