from flask import Flask, make_response, request, jsonify
from flask_cors import CORS
import os
from openai import AzureOpenAI
import re

model = "gpt-4-standard"
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),  
    api_version="2024-02-01",
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
)

app = Flask("excalidraw-ai-backend")
allowed_origin = os.getenv('ALLOWED_ORIGIN')
if allowed_origin:
    CORS(app, resources={r"/*": {"origins": allowed_origin}})
else:
    CORS(app)

@app.route('/v1/ai/text-to-diagram/generate', methods=['POST'])
def generate_diagram():
    data = request.get_json()
    prompt = data.get('prompt', '')

    # Call the OpenAI API
    response = client.chat.completions.create(model=model,
    messages=[
          {"role": "system", "content": "You are a mermaid diagram expert. Visualize the following user prompt in a mermaid diagram and return the code for the diagram. Only return the mermaid code and no additional text. Do not include the user prompt in the response."},
          {"role": "user", "content": prompt},
      ])

    response_content = response.choices[0].message.content

    stripped_response = re.sub(r'^.*```mermaid\n', '', response_content)
    stripped_response = re.sub(r'\n```$', '', stripped_response)

    response = make_response(jsonify({"generatedResponse": stripped_response}))
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
