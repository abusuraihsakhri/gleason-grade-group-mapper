"""Deterministic offline chat stub; no external model provider is implemented."""
from .base import PHIGuard


class MockLLM:
    """Test-only conversational stub; never presents output as clinical analysis."""

    def __init__(self, system_name: str = "Gleason Grade Group Mapper"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name} offline mock]: No model inference or clinical "
            "verification was performed. Review the request with qualified "
            "reference materials."
        )


class LLMFactory:
    """Only the deterministic mock is available in this repository."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Gleason Grade Group Mapper"):
        if str(provider).lower() in ("mock", "deterministic", "test"):
            return MockLLM(system_name)
        raise ValueError(
            f"Model provider {provider!r} is not implemented; use 'mock'."
        )
