import os
import stripe
from dotenv import load_dotenv

# Carrega a chave do ambiente
load_dotenv('.env.stripe_sample')
load_dotenv() # Fallback

stripe.api_key = os.getenv("STRIPE_API_KEY")

def setup_catalog():
    if not stripe.api_key:
        print("❌ ERRO: STRIPE_API_KEY não encontrada no ambiente.")
        return

    print("🚀 Iniciando automação de criação de Catálogo no Stripe...")

    # Catálogo esperado
    catalog = [
        {
            "id_interno": "sentinela_tatica",
            "name": "Aporte Tático (1.000 CI)",
            "description": "Liberação de inteligência tática e relatórios.",
            "amount": 49700, # R$ 497,00 (em centavos)
        },
        {
            "id_interno": "sentinela_warroom",
            "name": "War Room (6.000 CI)",
            "description": "Arsenal de inteligência completo para gestão de crise.",
            "amount": 199700, # R$ 1.997,00
        },
        {
            "id_interno": "sentinela_nacional",
            "name": "Escala Nacional (25.000 CI)",
            "description": "Malha de IPs residenciais e suporte dedicado MAX.",
            "amount": 799700, # R$ 7.997,00
        }
    ]

    results = {}

    for item in catalog:
        print(f"\n🔄 Processando: {item['name']}...")
        try:
            # 1. Tenta buscar se o produto já existe usando o metadata interno
            products = stripe.Product.search(
                query=f"metadata['id_interno']:'{item['id_interno']}'",
                limit=1
            )
            
            if products.data:
                prod = products.data[0]
                print(f"   ✅ Produto já existe: {prod.id}")
                
                # Pega o preço padrão do produto existente
                if prod.default_price:
                    results[item['id_interno']] = prod.default_price
                    print(f"   ✅ Preço já associado: {prod.default_price}")
                else:
                    # Cria o preço se o produto existe mas não tem preço padrão
                    price = stripe.Price.create(
                        product=prod.id,
                        unit_amount=item["amount"],
                        currency="brl",
                    )
                    # Atualiza o produto para ter esse preço como padrão
                    stripe.Product.modify(prod.id, default_price=price.id)
                    results[item['id_interno']] = price.id
                    print(f"   ➕ Preço CRIADO e associado: {price.id}")
            else:
                # 2. Se não existe, cria Produto e Preço de uma vez
                prod = stripe.Product.create(
                    name=item["name"],
                    description=item["description"],
                    metadata={"id_interno": item["id_interno"]},
                    default_price_data={
                        "currency": "brl",
                        "unit_amount": item["amount"],
                    }
                )
                results[item['id_interno']] = prod.default_price
                print(f"   ➕ Produto e Preço CRIADOS com sucesso!")
                print(f"   - Prod ID: {prod.id}")
                print(f"   - Price ID: {prod.default_price}")

        except Exception as e:
            print(f"   ❌ ERRO ao processar {item['name']}: {e}")

    print("\n" + "="*50)
    print("🎯 CATÁLOGO CONFIGURADO! Copie as chaves abaixo:")
    print("="*50)
    print(f"STRIPE_STARTER_PRICE_ID={results.get('sentinela_tatica', 'ERRO')}")
    print(f"STRIPE_SQUAD_PRICE_ID={results.get('sentinela_warroom', 'ERRO')}")
    print(f"STRIPE_WARROOM_PRICE_ID={results.get('sentinela_nacional', 'ERRO')}")
    print("="*50)

if __name__ == "__main__":
    setup_catalog()
