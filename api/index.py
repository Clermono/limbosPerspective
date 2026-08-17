from http.server import BaseHTTPRequestHandler
from upstash_redis import Redis

redis = Redis.from_env()

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        html_content = redis.get("site_html")
        
        if not html_content:
            html_content = "<h1>System is initializing. Check back in a few minutes!</h1>"

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))