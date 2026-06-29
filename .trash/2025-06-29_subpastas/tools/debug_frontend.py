
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import http.server
import socketserver
import os
import sys

# Configuração da Porta
PORT = 8080

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Injeção de headers para forçar a invalidação de cache (crucial para ES Modules)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        # CORS para testar chamadas de API externas se necessário
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        # Destacar requisições com erro (400+) no terminal
        status_code = int(args[1]) if len(args) > 1 and args[1].isdigit() else 200
        if status_code >= 400:
            sys.stderr.write(f"🔴 ERRO {status_code}: {self.address_string()} - {format%args}\n")
        else:
            sys.stdout.write(f"🟢 OK {status_code}: {self.address_string()} - {format%args}\n")

if __name__ == "__main__":
    # Garantir que o servidor roda a partir da raiz do projeto para localizar index.html e src/
    # Se o script for criado na pasta tools/, voltamos um nível
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Se o script for criado na raiz, project_root será o pai da raiz. Ajustamos.
    if not os.path.exists(os.path.join(project_root, "index.html")):
        project_root = os.getcwd()
        
    os.chdir(project_root)
    
    # Permitir reuso da porta
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), NoCacheHTTPRequestHandler) as httpd:
        print("="*60)
        print(f"🚀 Sentinela Frontend Debug Server iniciado.")
        print(f"📂 Diretório Base: {project_root}")
        print(f"🌐 Acesse no navegador: http://localhost:{PORT}")
        print("="*60)
        print("⚠️ Monitorando logs de rede. Erros 400+ (como os do AdSense) aparecerão aqui em vermelho.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor encerrado.")
            httpd.server_close()
            sys.exit(0)
