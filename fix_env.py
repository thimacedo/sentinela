import os

env_path = '.env'
if os.path.exists(env_path):
    with open(env_path, 'rb') as f:
        content = f.read()
    
    # Remove null characters and rewrite as UTF-8
    clean_content = content.replace(b'\x00', b'')
    
    with open(env_path, 'wb') as f:
        f.write(clean_content)
    print("Arquivo .env limpo de caracteres nulos.")
else:
    print(".env não encontrado.")
