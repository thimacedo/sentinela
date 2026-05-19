import os
import re
import logging
from mcp.server.fastmcp import FastMCP

# Configuração do servidor MCP
mcp = FastMCP("StandardValidator")

# Configuração de logging obrigatória
LOG_FILE = 'error.log'

@mcp.tool()
def validate_worker_standard(code: str) -> str:
    """
    Analisa o código Python para garantir conformidade com os padrões estabelecidos.

    Args:
        code (str): O código fonte completo a ser validado.

    Returns:
        str: Relatório de validação em formato de texto.

    Raises:
        Exception: Registra falhas de permissão ou leitura no error.log.
    """
    issues = []
    
    try:
        # 1. Verificação de Raw Strings para caminhos Windows
        if ":" in code and not re.search(r"r'|r\"", code):
            issues.append("ERRO: Caminhos de diretório detectados sem o prefixo de raw string (r'').")

        # 2. Verificação de Tratamento de Exceções e Log
        if "try:" not in code or "except" not in code:
            issues.append("ERRO: Bloco try-except obrigatório ausente.")
        
        if "error.log" not in code:
            issues.append("ERRO: Falha ao registrar erros no arquivo 'error.log'.")

        # 3. Verificação de Google Style Docstrings
        required_sections = ["Args:", "Returns:"]
        for section in required_sections:
            if section not in code:
                issues.append(f"ERRO: Documentação 'Google Style' ausente ou incompleta (Seção {section}).")

        # 4. Verificação de bibliotecas específicas (ex: mutagen para rádio)
        if (".m3u" in code or ".lst" in code) and "mutagen" not in code:
            issues.append("AVISO: Scripts de playlist ZaraRadio devem utilizar mutagen para metadados ID3.")

        if not issues:
            return "✅ PADRÃO OK: O código cumpre todos os requisitos de segurança e documentação."
        
        return "❌ VIOLAÇÕES DE PADRÃO ENCONTRADAS:\n- " + "\n- ".join(issues)

    except Exception as e:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"Falha na validação: {str(e)}\n")
        return f"Erro interno no validador. Verifique o {LOG_FILE}."

if __name__ == "__main__":
    mcp.run()
