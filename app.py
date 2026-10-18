from flask import Flask, make_response, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from openai import AzureOpenAI, OpenAIError
import re

allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGIN", "").split(",") if o.strip()]
if not allowed_origins:
    raise RuntimeError("ALLOWED_ORIGIN must be set")

rate_limit = os.getenv("RATE_LIMIT", "10 per minute;100 per day")
max_prompt_length = int(os.getenv("MAX_PROMPT_LENGTH", "2000"))
trusted_proxy_count = int(os.getenv("TRUSTED_PROXY_COUNT", "1"))

model = os.getenv("AZURE_OPENAI_MODEL")
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
)

app = Flask("excalidraw-ai-backend")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
if trusted_proxy_count > 0:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=trusted_proxy_count)

CORS(app, resources={r"/v1/ai/*": {"origins": allowed_origins, "methods": ["POST", "OPTIONS"]}})

# In-memory storage is only consistent with a single gunicorn worker.
limiter = Limiter(get_remote_address, app=app, storage_uri="memory://", headers_enabled=True)


def error_response(message, status):
    return make_response(jsonify({"error": message}), status)


@app.errorhandler(400)
def bad_request(_):
    return error_response("Bad request", 400)


@app.errorhandler(413)
def payload_too_large(_):
    return error_response("Payload too large", 413)


@app.errorhandler(429)
def too_many_requests(_):
    return error_response("Too many requests", 429)


@app.route('/v1/ai/text-to-diagram/generate', methods=['POST'])
@limiter.limit(rate_limit, methods=["POST"])
def generate_diagram():
    data = request.get_json(silent=True)
    prompt = data.get('prompt') if isinstance(data, dict) else None
    if not isinstance(prompt, str) or not prompt.strip():
        return error_response("Field 'prompt' must be a non-empty string", 400)
    prompt = prompt.strip()
    if len(prompt) > max_prompt_length:
        return error_response(f"Field 'prompt' must not exceed {max_prompt_length} characters", 400)

    try:
        response = client.chat.completions.create(model=model,
        messages=[
              {"role": "system", "content": "You are a mermaid diagram expert. Visualize the following user prompt in a mermaid diagram and return the code for the diagram. Only return the mermaid code and no additional text. Do not include the user prompt in the response."},
              {"role": "user", "content": prompt},
          ])
    except OpenAIError:
        app.logger.exception("OpenAI request failed")
        return error_response("Upstream service error", 502)

    response_content = response.choices[0].message.content if response.choices else None
    if not response_content:
        return error_response("Upstream service returned no content", 502)

    stripped_response = re.sub(r'^.*```mermaid\n', '', response_content)
    stripped_response = re.sub(r'\n```$', '', stripped_response)

    response = make_response(jsonify({"generatedResponse": stripped_response}))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
