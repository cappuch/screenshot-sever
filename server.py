from flask import Flask, request, send_from_directory, jsonify, abort
import os
import secrets
import yaml

config_path = os.path.join(os.path.dirname(__file__), 'config.yml')
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        if 'auth_token' in config:
            AUTH_KEY = config['auth_token']
            print('auth_token loaded from config file')
        else:
            AUTH_KEY = secrets.token_hex(16)
            print(f"ALERT! No auth_token found in {config_path}. Generating a new one: {AUTH_KEY}")

        if 'port' in config:
            PORT = config['port']
            print(f"Port loaded from config file: {PORT}")
        else:
            PORT = 5000
            print(f"ALERT! No port found in {config_path}. Using default port: {PORT}")
else:
    AUTH_KEY = secrets.token_hex(16)
    with open(config_path, 'w') as f:
        yaml.dump({'auth_token': AUTH_KEY, 'port': 5000}, f)
    print(f"ALERT! No config file found. Generating a new one: {config_path}")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app = Flask(__name__)

def generate_filename(original_filename):
    ext = ""
    if '.' in original_filename:
        ext = original_filename.rsplit('.', 1)[1]
    random_name = secrets.token_hex(4) # 8 chars
    return f"{random_name}.{ext}" if ext else random_name


@app.route('/upload', methods=['POST'])
def upload_file():
    if request.headers.get('Authorization') != AUTH_KEY: # amazing security (is this how it works?)
        abort(401)
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    new_filename = generate_filename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, new_filename)
    file.save(filepath)
    
    file_url = request.host_url + "files/" + new_filename
    return jsonify({"url": file_url})


@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# just a lil bit of security through obscurity 😎
@app.route('/robots.txt')
def robots():
    return "User-agent: *\nDisallow: /" # plz no index

if __name__ == '__main__':
    app.run("0.0.0.0", port=PORT)