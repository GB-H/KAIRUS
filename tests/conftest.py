"""
Configuracao compartilhada para todos os testes do KAIRUS.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from ai.memory import clear_memory


@pytest.fixture
def client():
    """Cliente HTTP para testar endpoints."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_memory():
    """Limpa a memoria antes de cada teste."""
    yield
    # Cleanup depois do teste
    from ai.memory import _active_memories
    _active_memories.clear()