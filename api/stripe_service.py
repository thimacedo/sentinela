import stripe
import os
from typing import Optional
from fastapi import HTTPException

# CONFIGURAÇÃO DE ELITE (Stripe SDK v15.x compatible)
stripe.api_key = os.getenv("STRIPE_API_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

class PaymentManager:
    """Gerencia o fluxo de Créditos de Inteligência (CI) do Sentinela."""

    @staticmethod
    def create_checkout_session(user_id: str, package_type: str):
        """Cria uma sessão de checkout para compra de pacotes de CI."""
        
        # Mapeia o tipo de pacote para o respectivo Stripe Price ID do catálogo
        package_map = {
            "tatica": {
                "price_id": os.getenv("STRIPE_STARTER_PRICE_ID"),
                "ci_amount": 1000
            },
            "warroom": {
                "price_id": os.getenv("STRIPE_SQUAD_PRICE_ID"),
                "ci_amount": 6000 # 5k + 1k bonus
            },
            "nacional": {
                "price_id": os.getenv("STRIPE_WARROOM_PRICE_ID"),
                "ci_amount": 25000
            }
        }

        package_info = package_map.get(package_type)
        if not package_info or not package_info["price_id"]:
            raise HTTPException(status_code=400, detail=f"Pacote '{package_type}' inválido ou Price ID não configurado no servidor.")

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card', 'pix'], # Adicionado PIX nativo do Stripe
                line_items=[{
                    'price': package_info["price_id"],
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/alvos?payment=success",
                cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/planos?payment=cancel",
                metadata={
                    "user_id": user_id,
                    "ci_amount": package_info["ci_amount"],
                    "package_type": package_type,
                    "type": "ci_topup"
                }
            )
            return session.url
        except stripe.error.StripeError as e:
            # Tratamento formal de erro conforme documentação v15
            raise HTTPException(status_code=e.http_status or 400, detail=str(e.user_message or e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

payment_manager = PaymentManager()
