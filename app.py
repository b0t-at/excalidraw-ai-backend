from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": os.getenv('ALLOWED_HOST')}})

@app.route('/v1/ai/text-to-diagram/generate', methods=['POST'])
def generate_diagram():
    data = request.get_json()
    prompt = data.get('prompt', '')

    # Call the OpenAI API
    response = openai.ChatCompletion.create(
      model="gpt-4-1106-preview",
      messages=[
            {"role": "system", "content": "Translate the following user prompt into a diagram."},
            {"role": "user", "content": prompt},
        ],
    )

    messages = response['choices'][0]['message']
    return jsonify({"generatedResponse": ''.join(message['content'] for message in messages)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)