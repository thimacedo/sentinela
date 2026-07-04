# -*- coding: utf-8 -*-
"""
Testes do ContextClassifier v1.0
Valida que comentarios de aniversario e celebracoes nao sao classificados como odio.
"""
import pytest
import sys
import os

# Adiciona o diretorio raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.context_classifier import ContextClassifier, context_classifier


class TestContextClassifier:
    """Testes para o detector de contextos positivos."""

    # === CASOS DE ANIVERSARIO (falsos positivos reportados) ===
    def test_parabens_amigo_deus_abencoe(self):
        text = "Parabens meu amigo Deus abençoe sua vida tudo de bom pra vc e sua familia"
        assert context_classifier.is_positive_context(text) is True

    def test_feliz_aniversario_irmao(self):
        text = "Parabens!!!! Feliz aniversario amigo e irmao. Muitos anos de vida"
        assert context_classifier.is_positive_context(text) is True

    def test_parabens_tudo_de_bom(self):
        text = "Parabens !!!! Meu amigo tudo de bom pra vc. Felicidades"
        assert context_classifier.is_positive_context(text) is True

    def test_feliz_niver(self):
        text = "Feliz niver, irmao! Muitas felicidades!"
        assert context_classifier.is_positive_context(text) is True

    # === CASOS DE AGRADECIMENTO ===
    def test_obrigado_deus_abencoe(self):
        text = "Obrigado amigo! Deus te abençoe sempre!"
        assert context_classifier.is_positive_context(text) is True

    # === CASOS DE SAUDACAO POSITIVA ===
    def test_bom_dia_abencoado(self):
        text = "Bom dia abençoado a todos!"
        assert context_classifier.is_positive_context(text) is True

    # === CASOS QUE NAO DEVEM SER CLASSIFICADOS COMO POSITIVOS ===
    def test_parabens_com_insulto(self):
        # "Parabens" mas com insulto — nao eh contexto positivo
        text = "Parabens seu idiota, voce conseguiu estragar tudo"
        assert context_classifier.is_positive_context(text) is False

    def test_parabens_sarcastico_politico(self):
        # Sarcasmo politico — nao eh contexto positivo
        text = "Parabens governo, mais uma vez voce mostrou incompetencia"
        assert context_classifier.is_positive_context(text) is False

    def test_texto_neutro(self):
        # Texto neutro sem contexto claro
        text = "Concordo com a proposta apresentada ontem"
        assert context_classifier.is_positive_context(text) is False

    def test_ataque_direto(self):
        # Ataque direto — nao eh contexto positivo
        text = "Você eh um verme, lixo humano"
        assert context_classifier.is_positive_context(text) is False

    def test_texto_vazio(self):
        assert context_classifier.is_positive_context("") is False

    def test_texto_curto_demais(self):
        assert context_classifier.is_positive_context("oi") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
