import os
from google import genai
from google.genai import types
from upstash_redis import Redis
from http.server import BaseHTTPRequestHandler

gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
redis = Redis.from_env()

def getNews():
    prompt = """
    Identify major breaking news happening right now in Science, Technology and Politics, 1 each.
    Return a structured summary with headlines, short bullet points and overall societal mood.
    """

    response = gemini_client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return response.text

def changeCode(currHTML, news):
    system_instruction = """
    You are an autonomous UI/UX system that constantly rewrites a website hourly.
    Rules:
    1. Read the provided HTML state and News.
    2. Overhaul the HTML/CSS/JS to reflect the news and mood.
    3. Use inline Tailwind CSS CDN (<script src="https://cdn.tailwindcss.com"></script>).
    4. MUST output raw executable single-file HTML code ONLY. Do not write markdown code blocks (```html) or conversational filler.
    5. Be politically neutral and do not sugarcoat conflicts or depressing or otherwise negative political news.
    """

    prompt = f"""
    - CURRENT WEBSITE STATE -
    {currHTML}

    - LATEST NEWS -
    {news}

    Rewrite the website to add this new state.
    """

    response = gemini_client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=1.0
        )
    )

    clean_code = response.text.replace("```html", "").replace("```", "").strip()
    return clean_code

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        raw_html = redis.get("site_html")
        currHTML = raw_html.decode("utf-8") if isinstance(raw_html, bytes) else raw_html

        if not currHTML:
            currHTML = """
            <!DOCTYPE html>
            <html>
            <head><script src="[https://cdn.tailwindcss.com](https://cdn.tailwindcss.com)"></script></head>
            <body class="bg-black text-white p-10 font-mono">
                <h1 class="text-3xl text-green-500">System Initializing...</h1>
                <p>Waiting for the first evolution cycle.</p>
            </body>
            </html>
            """

        try:
            news_payload = getNews()
            news_html = changeCode(currHTML, news_payload)

            redis.set("site_html", news_html)

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Loop executed. Site evolved successfully")
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Loop failed: {str(e)}".encode("utf-8"))