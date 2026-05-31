import json

def create_pr(branch: str, title: str, body: str) -> dict:
    """Retorna o payload esperado para o MCP GitHub criar um Pull Request.
    O agente de IA deve enviar esse dicionário como ferramenta `github.create_pull_request`.
    """
    return {
        "tool": "github.create_pull_request",
        "parameters": {
            "branch": branch,
            "title": title,
            "body": body
        }
    }
