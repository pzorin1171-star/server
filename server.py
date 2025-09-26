from flask import Flask, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'prod-secret-key')

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Маршрут для главной страницы
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Маршрут для статических файлов
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# API маршрут для проверки
@app.route('/api/health')
def health():
    return {'status': 'healthy', 'message': 'Server is running'}

# WebSocket
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Server starting on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
