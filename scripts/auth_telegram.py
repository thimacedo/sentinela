import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv(override=True)

api_id = os.getenv('TG_API_ID')
api_hash = os.getenv('TG_API_HASH')

if not api_id or not api_hash or api_id == 'your_telegram_api_id':
    print("❌ ERRO: TG_API_ID e TG_API_HASH não estão configurados no .env")
    print("Por favor, obtenha suas credenciais em https://my.telegram.org e adicione ao .env")
    exit(1)

# O session name 'discovery_session' irá criar o arquivo discovery_session.session
client = TelegramClient('discovery_session', int(api_id), api_hash)

async def main():
    print("Iniciando processo de autenticação do Telegram...")
    # O método start() solicita telefone e código interativamente no console
    await client.start()
    print("✅ Autenticação concluída com sucesso!")
    print("O arquivo 'discovery_session.session' foi criado localmente.")
    print("Agora o Sentinela pode se conectar ao Telegram sem intervenção manual.")
    
    # Busca informações do próprio perfil para validar
    me = await client.get_me()
    print(f"Logado como: {me.first_name} (@{me.username})")

if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
