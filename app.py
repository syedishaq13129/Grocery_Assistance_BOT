from flask import Flask, request, jsonify, render_template_string
import boto3
import json
import os
from decimal import Decimal

app = Flask(__name__)

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
bedrock = boto3.client('bedrock-runtime', region_name='ap-south-1')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grocery Assistant Bot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .chat-container {
            width: 90%;
            max-width: 800px;
            height: 80vh;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        }
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .message {
            max-width: 80%;
            padding: 15px 20px;
            border-radius: 20px;
            opacity: 0;
            animation: fadeIn 0.3s ease-in forwards;
        }
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 5px;
        }
        .bot-message {
            background: #f1f3f4;
            color: #333;
            align-self: flex-start;
            border-bottom-left-radius: 5px;
        }
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
            display: flex;
            gap: 10px;
        }
        .chat-input input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        .chat-input input:focus {
            border-color: #667eea;
        }
        .chat-input button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .chat-input button:hover {
            transform: translateY(-2px);
        }
        .loading {
            display: flex;
            gap: 5px;
            padding: 15px 20px;
        }
        .loading-dot {
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            animation: pulse 1.4s ease-in-out infinite both;
        }
        .loading-dot:nth-child(1) { animation-delay: -0.32s; }
        .loading-dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes fadeIn {
            to { opacity: 1; }
        }
        @keyframes pulse {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            🛒 Grocery Assistant Bot
        </div>
        <div class="chat-messages" id="messages">
            <div class="message bot-message">
                Hello! I'm your Grocery Assistant. I can help you with inventory management and recipe suggestions. Try asking me:
                <br><br>
                • "What's in my inventory?"<br>
                • "Show me available recipes"<br>
                • "What can I cook with chicken?"
            </div>
        </div>
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Type your message..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage(message, 'user');
            input.value = '';
            
            showLoading();
            
            fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                addMessage(data.response, 'bot');
            })
            .catch(error => {
                hideLoading();
                addMessage('Sorry, something went wrong. Please try again.', 'bot');
            });
        }

        function addMessage(text, sender) {
            const messagesContainer = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.textContent = text;
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function showLoading() {
            const messagesContainer = document.getElementById('messages');
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message bot-message loading';
            loadingDiv.id = 'loading';
            loadingDiv.innerHTML = '<div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div>';
            messagesContainer.appendChild(loadingDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

        function hideLoading() {
            const loading = document.getElementById('loading');
            if (loading) {
                loading.remove();
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get inventory data
        inventory_table = dynamodb.Table('GroceryInventory')
        inventory_response = inventory_table.scan()
        inventory_items = inventory_response.get('Items', [])
        
        # Get recipes data
        recipes_table = dynamodb.Table('GroceryRecipes')
        recipes_response = recipes_table.scan()
        recipes_items = recipes_response.get('Items', [])
        
        # Prepare context for AI
        inventory_text = json.dumps(inventory_items, cls=DecimalEncoder, indent=2)
        recipes_text = json.dumps(recipes_items, cls=DecimalEncoder, indent=2)
        
        prompt = f"""You are a helpful grocery inventory assistant. You have access to the user's current inventory and available recipes.

Current Inventory:
{inventory_text}

Available Recipes:
{recipes_text}

User Question: {user_message}

Please provide a helpful response based on the inventory and recipes available. Be conversational and practical."""
        
        # Call Bedrock
        bedrock_body = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 1000,
            "anthropic_version": "bedrock-2023-05-31"
        }
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(bedrock_body)
        )
        
        response_body = json.loads(response['body'].read())
        ai_response = response_body['content'][0]['text']
        
        return jsonify({'response': ai_response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
