from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'simple-secret-key-123')

# Явно указываем CORS
CORS(app, resources={r"/*": {"origins": "*"}})

try:
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        logger=True,
        engineio_logger=True
    )
    logger.info("Socket.IO initialized successfully")
except Exception as e:
    logger.error(f"Socket.IO initialization failed: {e}")
    raise

@app.route('/')
def home():
    logger.info("Home route accessed")
    return {'status': 'Server is running!', 'message': 'Tic-Tac-Toe Server'}

@app.route('/health')
def health():
    return {'status': 'healthy'}

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        logger.info(f"Starting server on port {port}")
        # Используем более простой метод запуска
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=port, 
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise
