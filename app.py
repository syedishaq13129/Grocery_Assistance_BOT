from flask import Flask, request, jsonify
import json
import boto3
from decimal import Decimal

app = Flask(__name__)

bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def get_inventory_data():
    try:
        table = dynamodb.Table('GroceryInventory')
        response = table.scan()
        return response['Items']
    except Exception as e:
        return []

def get_recipes_data():
    try:
        table = dynamodb.Table('GroceryRecipes')
        response = table.scan()
        return response['Items']
    except Exception as e:
        return []

def generate_chat_response(user_message, inventory, recipes):
    try:
        context = f"""You are a helpful grocery inventory assistant. 

Current Inventory:
{json.dumps(inventory, indent=2, default=decimal_default)}

Available Recipes:
{json.dumps(recipes, indent=2, default=decimal_default)}

Answer questions about inventory levels, product availability, and recipe suggestions based on available ingredients."""

        request_body = {
            "messages": [{"role": "user", "content": f"{context}\n\nUser Question: {user_message}"}],
            "max_tokens": 1000,
            "anthropic_version": "bedrock-2023-05-31"
        }
        
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def home():
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grocery Inventory Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 800px;
            width: 100%;
            height: 600px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 28px;
            margin-bottom: 5px;
        }
        
        .header p {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        
        .message.user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            border-bottom-left-radius: 4px;
        }
        
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }
        
        #user-input {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 15px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        #user-input:focus {
            border-color: #667eea;
        }
        
        #send-btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 15px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        #send-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        #send-btn:active {
            transform: translateY(0);
        }
        
        #send-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #667eea;
            animation: pulse 1.4s infinite ease-in-out;
        }
        
        @keyframes pulse {
            0%, 80%, 100% { opacity: 0.3; }
            40% { opacity: 1; }
        }
        
        .welcome-message {
            text-align: center;
            color: #666;
            padding: 40px 20px;
        }
        
        .welcome-message h2 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #764ba2;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛒 Grocery Inventory Assistant</h1>
            <p>Ask me about inventory, recipes, or product availability</p>
        </div>
        
        <div class="chat-container" id="chat-container">
            <div class="welcome-message">
                <h2>Welcome!</h2>
                <p>Ask me anything about our grocery inventory or recipes.</p>
                <p style="margin-top: 10px; font-size: 13px;">Try: "What items are low in stock?" or "Show me recipes with chicken"</p>
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="user-input" placeholder="Type your message here..." />
            <button id="send-btn">Send</button>
        </div>
    </div>

    <script>
        const chatContainer = document.getElementById('chat-container');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');
        
        function addMessage(content, isUser) {
            const welcomeMsg = chatContainer.querySelector('.welcome-message');
            if (welcomeMsg) {
                welcomeMsg.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function addLoadingMessage() {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';
            messageDiv.id = 'loading-message';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = '<span class="loading"></span> <span class="loading"></span> <span class="loading"></span>';
            
            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function removeLoadingMessage() {
            const loadingMsg = document.getElementById('loading-message');
            if (loadingMsg) {
                loadingMsg.remove();
            }
        }
        
        async function sendMessage() {
            const message = userInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            userInput.value = '';
            sendBtn.disabled = true;
            
            addLoadingMessage();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                removeLoadingMessage();
                addMessage(data.response, false);
            } catch (error) {
                removeLoadingMessage();
                addMessage('Sorry, there was an error processing your request.', false);
                console.error('Error:', error);
            }
            
            sendBtn.disabled = false;
            userInput.focus();
        }
        
        sendBtn.addEventListener('click', sendMessage);
        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        userInput.focus();
    </script>
</body>
</html>'''

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        inventory = get_inventory_data()
        recipes = get_recipes_data()
        response = generate_chat_response(user_message, inventory, recipes)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
