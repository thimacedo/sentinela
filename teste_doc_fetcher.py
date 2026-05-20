from workers.ai.doc_fetcher import DocFetcher
import os

def test_doc_fetcher():
    # Setup
    fetcher = DocFetcher(cache_dir="workers/config/api_docs")
    
    # Execução
    content = fetcher.get_relevant("instagram")
    
    # Validação
    assert content is not None, "Falha: Doc não encontrado"
    assert "Rate limit: 200/h" in content, "Falha: Conteúdo incorreto"
    
    print("✅ DocFetcher: get_relevant('instagram') → OK")
    
    # Teste de refresh (simulado)
    fetcher.refresh_all()
    print("✅ DocFetcher: refresh_all() → OK")

if __name__ == "__main__":
    test_doc_fetcher()
