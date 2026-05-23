import stripe
import os
from typing import Optional
from fastapi import HTTPException

# CONFIGURAÇÃO DE ELITE
stripe.api_key = os.getenv("STRIPE_API_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

class PaymentManager:
    """Gerencia o fluxo de créditos do Sentinela."""

    @staticmethod
    def create_checkout_session(user_id: str, stn_amount: int):
        """Cria uma sessão de checkout para compra de tokens STN."""
        try:
            # R$ 1,00 por 10 STN
            unit_amount = int((stn_amount / 10) * 100) # centavos

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'brl',
                        'product_data': {
                            'name': f'Pack {stn_amount} STN - Créditos de Inteligência',
                            'description': 'Tokens para desbloqueio de dados e geração de relatórios detalhados.',
                        },
                        'unit_amount': unit_amount,
                    },
                    'quantity': 1,
                }],

                mode='payment',
                success_url=f"{os.getenv('FRONTEND_URL')}/#monitor?success=true",
                cancel_url=f"{os.getenv('FRONTEND_URL')}/#pricing?cancel=true",
                metadata={
                    "user_id": user_id,
                    "stn_amount": stn_amount,
                    "type": "stn_topup"
                }
            )
            return session.url
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @staticmethod
    def generate_pix_payload(amount: float):
        """Simulação de geração de PIX via gateway (ex: MercadoPago ou Juno)."""
        # Aqui integraria com o SDK do gateway PIX
        return {
            "qr_code": "00020126580014BR.GOV.BCB.PIX...",
            "copy_paste": "pix-payload-sentinela-diamond-v20.3"
        }

payment_manager = PaymentManager()
