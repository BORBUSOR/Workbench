import os
import random
from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest

load_dotenv()
app = Flask(__name__)

# Global array to hold all banks linked during the current browser session
SESSION_TOKENS = []

configuration = plaid.Configuration(
    host=plaid.Environment.Production,
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET'),
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Haushold CFO: Plaid Link</title>
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <style>
        body { font-family: Arial, sans-serif; display: flex; flex-direction: column; align-items: center; margin-top: 80px; background-color: #313338; color: white;}
        button { padding: 15px 30px; font-size: 18px; cursor: pointer; border: none; border-radius: 5px; font-weight: bold; transition: 0.2s; margin: 10px;}
        #link-button { background-color: #5865F2; color: white; }
        #link-button:hover { background-color: #4752C4; }
        #finish-button { background-color: #23A559; color: white; display: none; }
        #finish-button:hover { background-color: #1D8B4A; }
        .container { background-color: #2B2D31; padding: 40px; border-radius: 10px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.2); min-width: 400px; }
        h1 { margin-top: 0; }
        #status { margin-top: 20px; font-size: 16px; color: #B5BAC1; }
    </style>
</head>
<body>
    <div class="container" id="main-container">
        <h1>🏦 Haushold CFO: Bank Link</h1>
        <p>Click below to securely log into your financial institutions.</p>
        <div id="status">Banks connected this session: <strong style="color: #5865F2; font-size: 20px;" id="bank-count">0</strong></div>
        <br>
        <button id="link-button">Connect a Bank</button>
        <br>
        <button id="finish-button">End Session & Get PIN</button>
    </div>
    
    <script>
        let banksConnected = 0;

        document.getElementById('link-button').onclick = async function() {
            const response = await fetch('/create_link_token', { method: 'POST' });
            const data = await response.json();
            
            const handler = Plaid.create({
                token: data.link_token,
                onSuccess: async function(public_token, metadata) {
                    await fetch('/exchange_public_token', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ public_token: public_token })
                    });
                    
                    // Update UI after a successful link
                    banksConnected++;
                    document.getElementById('bank-count').innerText = banksConnected;
                    document.getElementById('link-button').innerText = "Link Another Bank";
                    document.getElementById('finish-button').style.display = "inline-block";
                },
                onExit: function(err, metadata) { console.log('Exit:', err, metadata); }
            });
            handler.open();
        };

        document.getElementById('finish-button').onclick = async function() {
            const response = await fetch('/finish_session', { method: 'POST' });
            const data = await response.json();
            
            document.getElementById('main-container').innerHTML = `
                <h1>✅ Session Complete!</h1>
                <p style="font-size: 18px;">You successfully linked <strong>${banksConnected}</strong> accounts.</p>
                <div style="background-color: #1E1F22; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 0; color: #B5BAC1; font-size: 14px;">YOUR SECURE PIN</p>
                    <p style="font-size: 36px; margin: 10px 0; font-weight: bold; letter-spacing: 5px; color: #23A559;">${data.pin}</p>
                </div>
                <p>You can close this window and run <code>!claimtoken ${data.pin}</code> in Discord.</p>
            `;
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    global SESSION_TOKENS
    SESSION_TOKENS = [] # Clear any hanging tokens if the user refreshes the page
    return render_template_string(HTML_TEMPLATE)

@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    request_data = LinkTokenCreateRequest(
        products=[Products('transactions')],
        client_name="Haushold CFO",
        country_codes=[CountryCode('US')],
        language='en',
        user=LinkTokenCreateRequestUser(client_user_id="haushold_admin")
    )
    response = client.link_token_create(request_data)
    return jsonify(response.to_dict())

@app.route('/exchange_public_token', methods=['POST'])
def exchange_public_token():
    public_token = request.json['public_token']
    exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_response = client.item_public_token_exchange(exchange_request)
    access_token = exchange_response['access_token']
    
    # Store in memory temporarily instead of writing the file yet
    SESSION_TOKENS.append(access_token)
    print(f"✅ Bank connected! Current queue: {len(SESSION_TOKENS)}")
    
    return jsonify({'status': 'success'})

@app.route('/finish_session', methods=['POST'])
def finish_session():
    global SESSION_TOKENS
    pin = str(random.randint(1000, 9999))
    
    # Line 1 is the PIN, all subsequent lines are tokens
    with open('latest_token.txt', 'w') as f:
        f.write(f"{pin}\n")
        for token in SESSION_TOKENS:
            f.write(f"{token}\n")
            
    print("\n" + "="*60)
    print(f"🎉 SESSION COMPLETE! {len(SESSION_TOKENS)} banks linked.")
    print(f"🔒 YOUR SECURE PIN IS: {pin}")
    print(f"Turn your bot back on and run '!claimtoken {pin}' in Discord!")
    print("="*60 + "\n")
    
    SESSION_TOKENS = [] # Clear memory to secure it
    
    return jsonify({'status': 'success', 'pin': pin})

if __name__ == '__main__':
    print("\n🌐 Starting temporary Plaid Server... Open http://localhost:5000 in your browser.\n")
    app.run(port=5000)