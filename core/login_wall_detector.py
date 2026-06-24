"""
Detecção robusta de Login Walls, Sessions Expiradas e Challenges.
"""

import re
import logging
from typing import Tuple
from playwright.async_api import Page
from datetime import datetime

logger = logging.getLogger(__name__)


class LoginWallDetector:
    """Detecta com precisão se página é um muro de login"""
    
    # URLs que indicam login wall
    LOGIN_URL_PATTERNS = [
        r"accounts/login",
        r"accounts/account_recovery",
        r"^.*instagram\.com/accounts/",
        r"/login/?$",
        r"/signin/?$",
    ]
    
    # Títulos característicos
    LOGIN_TITLES = [
        "log in",
        "entrar",
        "login required",
        "instagram",  # Página de login fica só com "Instagram"
    ]
    
    # Textos de conteúdo que indicam login wall
    LOGIN_CONTENT_INDICATORS = [
        "log in to instagram",
        "faça login para curtir",
        "faça login para ver mais",
        "enter your login details",
        "forgot password",
        "didn't get the code?",
        "create new account",
        "sign up",
    ]
    
    CHALLENGE_INDICATORS = [
        "challenge",
        "suspicious login attempt",
        "tentativa de login suspeita",
        "verify your identity",
        "prove you're not a bot",
        "prove that you own the account",
    ]
    
    def __init__(self):
        self.logger = logger
    
    async def detect_login_wall(self, page: Page) -> Tuple[bool, dict]:
        """
        Detecta login wall com método robusto.
        
        Retorna:
            (is_login_wall, details_dict)
        """
        try:
            page_url = page.url.lower()
            page_title = (await page.title()).lower()
            page_content = (await page.content())[:10000].lower()
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao inspecionar página: {e}")
            return False, {"error": str(e)}
        
        details = {
            "url": page_url,
            "title": page_title,
            "is_login_wall": False,
            "matched_patterns": [],
        }
        
        # Check 1: URL patterns
        for pattern in self.LOGIN_URL_PATTERNS:
            if re.search(pattern, page_url, re.IGNORECASE):
                details["matched_patterns"].append(f"url_pattern:{pattern}")
                details["is_login_wall"] = True
                break
        
        # Check 2: Title
        for title_keyword in self.LOGIN_TITLES:
            if title_keyword in page_title:
                # Mas não é suficiente sozinho (muitas páginas têm "instagram" no título)
                if title_keyword != "instagram":
                    details["matched_patterns"].append(f"title:{title_keyword}")
                    details["is_login_wall"] = True
                    break
        
        # Check 3: Conteúdo (mais confiável)
        login_content_matches = sum(
            1 for indicator in self.LOGIN_CONTENT_INDICATORS
            if indicator in page_content
        )
        
        if login_content_matches >= 2:  # Pelo menos 2 indicadores
            details["matched_patterns"].append(f"content:{login_content_matches}_indicators")
            details["is_login_wall"] = True
        
        return details["is_login_wall"], details
    
    async def detect_challenge(self, page: Page) -> Tuple[bool, dict]:
        """Detecta Instagram Challenge / Soft Block"""
        try:
            page_url = page.url.lower()
            page_content = (await page.content())[:10000].lower()
        except:
            return False, {}
        
        details = {
            "url": page_url,
            "is_challenge": False,
            "challenge_type": None,
            "matched_indicators": [],
        }
        
        # Check 1: URL
        if "challenge" in page_url:
            details["is_challenge"] = True
            details["challenge_type"] = "url_based"
            details["matched_indicators"].append("challenge_in_url")
        
        # Check 2: Conteúdo
        for indicator in self.CHALLENGE_INDICATORS:
            if indicator in page_content:
                details["is_challenge"] = True
                details["challenge_type"] = "content_based"
                details["matched_indicators"].append(indicator)
                break
        
        return details["is_challenge"], details
    
    async def diagnose_page_state(self, page: Page) -> dict:
        """Diagnóstico completo do estado da página"""
        is_login, login_details = await self.detect_login_wall(page)
        is_challenge, challenge_details = await self.detect_challenge(page)
        
        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "url": page.url,
            "is_login_wall": is_login,
            "login_details": login_details,
            "is_challenge": is_challenge,
            "challenge_details": challenge_details,
            "state": self._determine_state(is_login, is_challenge),
        }
        
        return diagnosis
    
    def _determine_state(self, is_login: bool, is_challenge: bool) -> str:
        """Determina estado geral da página"""
        if is_login:
            return "login_wall"
        if is_challenge:
            return "challenge_required"
        return "normal"
