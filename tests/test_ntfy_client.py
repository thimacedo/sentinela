# tests/test_ntfy_client.py
"""Testes para core.ntfy_client."""
import os
import sys
import importlib
from unittest.mock import patch, MagicMock

import pytest

# Garante que o pacote `core` na raiz do projeto seja encontrado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def _reload_module(env: dict):
    """Recarrega core.ntfy_client com variáveis de ambiente controladas."""
    saved = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        import core.ntfy_client as ntfy
        importlib.reload(ntfy)
        return ntfy
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_default_url_quando_env_vazio():
    ntfy = _reload_module({})
    assert ntfy.NTFY_URL == "https://ntfy.sh/sentinela"


def test_url_customizada_quando_env_setado():
    ntfy = _reload_module({
        "NTFY_URL": "https://ntfy.exemplo.com",
        "NTFY_TOPIC": "meu-canal",
    })
    assert ntfy.NTFY_URL == "https://ntfy.exemplo.com/meu-canal"


def test_url_com_barra_no_final_e_normalizada():
    ntfy = _reload_module({
        "NTFY_URL": "https://ntfy.exemplo.com/",
        "NTFY_TOPIC": "canal",
    })
    assert ntfy.NTFY_URL == "https://ntfy.exemplo.com/canal"


def test_send_notification_monta_headers_corretos():
    ntfy = _reload_module({})
    with patch("core.ntfy_client.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        result = ntfy.send_notification(
            title="Teste",
            message="Olá",
            tags="robot",
            priority="high",
        )
        assert result is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://ntfy.sh/sentinela"
        assert kwargs["headers"]["Title"] == "Teste"
        assert kwargs["headers"]["Tags"] == "robot"
        assert kwargs["headers"]["Priority"] == "high"
        assert "Authorization" not in kwargs["headers"]


def test_send_notification_com_token_adiciona_bearer():
    ntfy = _reload_module({"NTFY_TOKEN": "tk_abc123"})
    with patch("core.ntfy_client.requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        ntfy.send_notification("T", "M")
        kwargs = mock_post.call_args.kwargs
        assert kwargs["headers"]["Authorization"] == "Bearer tk_abc123"


def test_send_notification_retorna_false_em_erro():
    ntfy = _reload_module({})
    with patch("core.ntfy_client.requests.post", side_effect=Exception("timeout")):
        assert ntfy.send_notification("T", "M") is False