"""Private loopback HTTP transport for the Python catalog assistant."""
import hmac
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Embedded Python does not automatically add the script directory to sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from radar_ai.poc_catalog import respond
from radar_ai.accounts import execute as account_execute, AccountError
from radar_ai.marketplace import execute as marketplace_execute
from radar_ai.accounts import connect,user_for
from radar_ai.journey import PROFILE,profile_for
from contextlib import closing

TOKEN = os.environ.get("RADAR_CHAT_TOKEN", "")
if not TOKEN:
    raise SystemExit("Inicie pelo npm start ou npm run dev: token interno ausente.")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Do not log private conversation content.

    def send_json(self, code, body):
        content = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        if self.path not in ("/chat", "/account", "/marketplace"):
            return self.send_json(404, {"error": "Rota não encontrada"})
        if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + TOKEN):
            return self.send_json(401, {"error": "Acesso não autorizado"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= (2900000 if self.path=='/marketplace' else 20000):
                return self.send_json(413, {"error": "Mensagem muito grande ou vazia"})
            self.connection.settimeout(10)
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("Corpo inválido")
            if self.path=='/marketplace':result=marketplace_execute(data.get('action'),data.get('data',{}),data.get('session_token',''))
            elif self.path=='/account':
                result=account_execute(data.get('action'),data.get('data',{}),data.get('session_token',''))
                if 'recommended_ids' in result:result['recommended_ids']=[]
            else:
                profile=None
                if data.get('session_token'):
                    try:
                        with closing(connect()) as db:
                            user=user_for(db,data['session_token'])
                            profile=profile_for(db,user['id']) or data.get('local_profile')
                            if profile:profile={**profile,'display_name':user['name']}
                    except AccountError:pass
                context=PROFILE.set(profile)
                try:result=respond(data.get("message"), data.get("state"))
                finally:PROFILE.reset(context)
            return self.send_json(200, result)
        except AccountError as error:
            return self.send_json(error.status, {'error': str(error)})
        except (ValueError, TypeError, UnicodeDecodeError):
            return self.send_json(400, {"error": "Mensagem ou contexto inválido"})
        except TimeoutError:
            return self.send_json(408, {"error": "Tempo de leitura excedido"})
        except Exception:
            return self.send_json(500, {"error": "Não foi possível consultar o catálogo"})


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    print(json.dumps({"ready": True, "port": server.server_address[1]}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
