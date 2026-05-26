import logging
import os
import re

logger = logging.getLogger("core.autopilot.patcher")

class Patcher:
    """
    Motor de intervenção que aplica correções no código-fonte (PASA v70.0).
    """
    def __init__(self, project_root: str = "."):
        self.project_root = project_root

    def apply_hotfix(self, file_path: str, old_string: str, new_string: str) -> bool:
        """Aplica uma correção cirúrgica em um arquivo."""
        abs_path = os.path.join(self.project_root, file_path)
        if not os.path.exists(abs_path):
            logger.error(f"Arquivo não encontrado para patch: {abs_path}")
            return False

        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if old_string not in content:
                logger.warning(f"String original não encontrada no arquivo {file_path}")
                return False

            new_content = content.replace(old_string, new_string, 1)
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            logger.info(f"✅ Hot-fix aplicado com sucesso em {file_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao aplicar hot-fix em {file_path}: {e}")
            return False

    def update_selector(self, scraper_file: str, old_selector: str, new_selector: str) -> bool:
        """Específico para atualizar seletores CSS/XPath."""
        return self.apply_hotfix(scraper_file, f"'{old_selector}'", f"'{new_selector}'")

patcher = Patcher()
