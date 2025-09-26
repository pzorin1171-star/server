from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'prod-secret-key')

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

games = {}

# Маршрут для главной страницы (фронтенд)
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

# Маршрут для других статических файлов (CSS, JS)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# API маршруты
@app.route('/api/health')
def health():
    return {'status': 'healthy'}

@app.route('/api/games')
def list_games():
    return {'active_games': len(games)}

# WebSocket handlers
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join')
def handle_join(data):
    game_id = data.get('game_id', 'default')
    print(f'Player joined game {game_id}')
    emit('joined', {'game_id': game_id})

@socketio.on('move')
def handle_move(data):
    print(f'Move: {data}')
    emit('move_made', data, broadcast=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Server starting on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
