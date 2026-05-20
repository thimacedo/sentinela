# main_orchestrator.py
import logging
from instagram_scraper import InstagramScraper
# Simulação do módulo PASA (Protocolo de Análise Semântica Avançada)
# from pasa_classifier import PASAEngine 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Orchestrator")

class PASAEngineMock:
    """Mock do classificador PASA para validar a arquitetura."""
    @staticmethod
    def classify_text(text: str) -> str:
        text_lower = text.lower()
        if any(word in text_lower for word in ["urgente", "denúncia", "fraude", "corrupção"]):
            return "CRITICAL"
        elif any(word in text_lower for word in ["apoio", "concordo", "parabéns"]):
            return "POSITIVE"
        elif any(word in text_lower for word in ["contra", "discordo", "péssimo"]):
            return "NEGATIVE"
        return "NEUTRAL"

class SentinelOrchestrator:
    def __init__(self, targets: list):
        self.targets = targets
        self.pasa_engine = PASAEngineMock()

    def run_collection_cycle(self):
        logger.info("Starting new data collection cycle...")
        all_results = []

        for target in self.targets:
            scraper = InstagramScraper(target_profile=target)
            posts = scraper.fetch_recent_posts()
            
            for post in posts:
                # Integração PASA: Classificando a legenda do post
                post["pasa_classification"] = self.pasa_engine.classify_text(post.get("text", ""))
                
                # Opcional: extrair e classificar comentários
                if post["comments_count"] > 0:
                    comments = scraper.fetch_comments(post["shortcode"])
                    for comment in comments:
                         comment["pasa_classification"] = self.pasa_engine.classify_text(comment.get("text", ""))
                    post["analyzed_comments"] = comments

                all_results.append(post)

        logger.info(f"Cycle completed. Processed {len(all_results)} items.")
        return all_results

if __name__ == "__main__":
    targets = ["camaradenatal", "prefeituradonatal"] # Exemplos locais do Sentinela
    orchestrator = SentinelOrchestrator(targets)
    orchestrator.run_collection_cycle()