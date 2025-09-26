from flask import Flask, request
from flask_socketio import SocketIO
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'online-tic-tac-toe-secret'

socketio = SocketIO(app, cors_allowed_origins="*")

# Простое хранилище игр
games = {}

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Крестики-нолики ONLINE</title>
        <style>
            body { font-family: Arial; text-align: center; margin: 50px; }
            .board { display: inline-grid; grid-template-columns: repeat(3, 100px); gap: 5px; margin: 20px; }
            .cell { width: 100px; height: 100px; border: 2px solid #333; font-size: 40px; cursor: pointer; }
            .cell.x { color: red; }
            .cell.o { color: blue; }
            #status { margin: 20px; padding: 10px; background: #f0f0f0; }
            .online { background: #d4edda; }
            .offline { background: #f8d7da; }
        </style>
    </head>
    <body>
        <h1>🎮 Крестики-нолики ONLINE</h1>
        <div id="status" class="offline">Статус: Отключено</div>
        
        <div>
            <input type="text" id="gameId" value="game1" placeholder="ID игры">
            <button onclick="connectToGame()">Присоединиться</button>
        </div>
        
        <div class="board" id="board"></div>
        <div>Игрок: <span id="playerSymbol">-</span></div>
        <div>Ход: <span id="currentTurn">-</span></div>
        
        <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
        <script>
            let socket = null;
            let currentPlayer = '';
            let board = ['', '', '', '', '', '', '', '', ''];
            let gameId = '';
            let isMyTurn = false;
            
            function createBoard() {
                const boardElement = document.getElementById('board');
                boardElement.innerHTML = '';
                
                for (let i = 0; i < 9; i++) {
                    const cell = document.createElement('div');
                    cell.className = 'cell';
                    cell.onclick = () => makeMove(i);
                    boardElement.appendChild(cell);
                }
                updateBoard();
            }
            
            function connectToGame() {
                gameId = document.getElementById('gameId').value || 'default';
                
                // Подключаемся к серверу
                socket = io();
                
                socket.on('connect', () => {
                    document.getElementById('status').textContent = 'Статус: Подключено к серверу';
                    document.getElementById('status').className = 'online';
                    
                    // Присоединяемся к игре
                    socket.emit('join', { game_id: gameId });
                });
                
                socket.on('game_start', (data) => {
                    currentPlayer = data.symbol;
                    isMyTurn = currentPlayer === 'X';
                    document.getElementById('playerSymbol').textContent = currentPlayer;
                    document.getElementById('currentTurn').textContent = isMyTurn ? 'X (Ваш ход)' : 'O (Ход соперника)';
                    document.getElementById('currentTurn').style.color = isMyTurn ? 'green' : 'red';
                });
                
                socket.on('board_update', (data) => {
                    board = data.board;
                    isMyTurn = data.current_turn === currentPlayer;
                    updateBoard();
                    document.getElementById('currentTurn').textContent = isMyTurn ? 
                        currentPlayer + ' (Ваш ход)' : 
                        (currentPlayer === 'X' ? 'O' : 'X') + ' (Ход соперника)';
                    document.getElementById('currentTurn').style.color = isMyTurn ? 'green' : 'red';
                });
                
                socket.on('game_over', (data) => {
                    if (data.winner === 'draw') {
                        alert('Ничья!');
                    } else {
                        alert(data.winner === currentPlayer ? 'Вы победили!' : 'Вы проиграли!');
                    }
                    setTimeout(resetGame, 2000);
                });
                
                socket.on('error', (data) => {
                    alert('Ошибка: ' + data.message);
                });
            }
            
            function makeMove(index) {
                if (isMyTurn && board[index] === '') {
                    socket.emit('move', {
                        game_id: gameId,
                        position: index,
                        symbol: currentPlayer
                    });
                }
            }
            
            function updateBoard() {
                const cells = document.querySelectorAll('.cell');
                cells.forEach((cell, index) => {
                    cell.textContent = board[index];
                    cell.className = `cell ${board[index]}`;
                    cell.style.cursor = isMyTurn && board[index] === '' ? 'pointer' : 'not-allowed';
                });
            }
            
            function resetGame() {
                socket.emit('restart', { game_id: gameId });
            }
            
            // Инициализация
            createBoard();
        </script>
    </body>
    </html>
    '''

@socketio.on('connect')
def handle_connect():
    logger.info(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('join')
def handle_join(data):
    game_id = data.get('game_id', 'default')
    
    if game_id not in games:
        # Создаем новую игру
        games[game_id] = {
            'board': ['', '', '', '', '', '', '', '', ''],
            'players': {'X': request.sid, 'O': None},
            'current_turn': 'X',
            'status': 'waiting'
        }
        # Первый игрок получает X
        socketio.emit('game_start', {'symbol': 'X'}, room=request.sid)
    else:
        game = games[game_id]
        if game['players']['O'] is None:
            # Второй игрок получает O
            game['players']['O'] = request.sid
            game['status'] = 'playing'
            
            # Уведомляем игроков
            socketio.emit('game_start', {'symbol': 'O'}, room=request.sid)
            socketio.emit('board_update', {
                'board': game['board'],
                'current_turn': 'X'
            }, room=game_id)
        else:
            socketio.emit('error', {'message': 'Комната заполнена'}, room=request.sid)

@socketio.on('move')
def handle_move(data):
    game_id = data.get('game_id')
    position = data.get('position')
    symbol = data.get('symbol')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    
    # Проверяем правильность хода
    if (game['current_turn'] != symbol or 
        game['players'][symbol] != request.sid or
        game['board'][position] != ''):
        return
    
    # Делаем ход
    game['board'][position] = symbol
    
    # Проверяем победу
    winner = check_winner(game['board'])
    if winner:
        socketio.emit('game_over', {'winner': winner}, room=game_id)
        # Авторестарт
        import time
        time.sleep(3)
        reset_game(game_id)
    elif all(cell != '' for cell in game['board']):
        socketio.emit('game_over', {'winner': 'draw'}, room=game_id)
        time.sleep(3)
        reset_game(game_id)
    else:
        # Меняем ход
        game['current_turn'] = 'O' if symbol == 'X' else 'X'
        socketio.emit('board_update', {
            'board': game['board'],
            'current_turn': game['current_turn']
        }, room=game_id)

@socketio.on('restart')
def handle_restart(data):
    game_id = data.get('game_id')
    if game_id in games:
        reset_game(game_id)
        socketio.emit('board_update', {
            'board': games[game_id]['board'],
            'current_turn': 'X'
        }, room=game_id)

def check_winner(board):
    # Комбинации для победы
    lines = [
        [0,1,2], [3,4,5], [6,7,8],  # rows
        [0,3,6], [1,4,7], [2,5,8],  # columns
        [0,4,8], [2,4,6]            # diagonals
    ]
    
    for a, b, c in lines:
        if board[a] and board[a] == board[b] and board[a] == board[c]:
            return board[a]
    return None

def reset_game(game_id):
    if game_id in games:
        games[game_id]['board'] = ['', '', '', '', '', '', '', '', '']
        games[game_id]['current_turn'] = 'X'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Онлайн сервер запускается на порту {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
