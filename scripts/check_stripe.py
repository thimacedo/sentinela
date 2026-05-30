import stripe
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('STRIPE_API_KEY')

print(f"--- Diagnóstico Stripe ---")
print(f"Chave STRIPE_API_KEY configurada: {'Sim' if key else 'Não'}")

if key:
    try:
        stripe.api_key = key
        # Tenta recuperar informações da conta conectada
        account = stripe.Account.retrieve()
        print(f"Status: Conectado")
        print(f"ID da Conta: {account.id}")
        print(f"Email: {account.email}")
        
        # Verifica saldo (modo live ou test)
        balance = stripe.Balance.retrieve()
        print(f"Modo: {'Live' if account.details_submitted else 'Test/Sandbox'}")
        print(f"Conexão estabelecida com sucesso.")
    except Exception as e:
        print(f"Erro na conexão Stripe: {e}")
else:
    print("O sistema está operando em MODO MOCK (Bypass) devido à ausência de credenciais.")
