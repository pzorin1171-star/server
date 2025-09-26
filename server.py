from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tic-tac-toe-secret-2024')

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Хранилище игр
games = {}
players = {}

@app.route('/')
def serve_frontend():
    return '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Крестики-нолики онлайн</title>
        <style>
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: 'Arial', sans-serif;
            }
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                max-width: 500px;
                width: 100%;
                text-align: center;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
                font-size: 2.5em;
            }
            .game-id-section {
                margin: 20px 0;
            }
            input {
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                width: 200px;
                margin-right: 10px;
            }
            button {
                background: #667eea;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 16px;
                transition: background 0.3s;
                margin: 5px;
            }
            button:hover {
                background: #5a6fd8;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .status {
                margin: 20px 0;
                padding: 15px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            .status.waiting {
                background: #fff3cd;
                color: #856404;
            }
            .status.playing {
                background: #d1ecf1;
                color: #0c5460;
            }
            .status.winner {
                background: #d4edda;
                color: #155724;
            }
            .board {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 10px;
                margin: 20px auto;
                max-width: 300px;
            }
            .cell {
                width: 100px;
                height: 100px;
                background: #f8f9fa;
                border: 3px solid #667eea;
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 2.5em;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s;
            }
            .cell:hover {
                background: #e9ecef;
                transform: scale(1.05);
            }
            .cell.x { color: #e74c3c; }
            .cell.o { color: #3498db; }
            .cell.winning {
                background: #2ecc71;
                color: white;
            }
            .cell:disabled {
                cursor: not-allowed;
                transform: none;
            }
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 Крестики-нолики</h1>
            
            <div id="connectionSection">
                <div class="game-id-section">
                    <input type="text" id="gameIdInput" placeholder="ID игры" value="game-1">
                    <button onclick="connectToGame()">Присоединиться к игре</button>
                </div>
                <div id="connectionStatus" class="status">Введите ID игры и нажмите "Присоединиться"</div>
            </div>

            <div id="gameSection" class="hidden">
                <div id="gameStatus" class="status"></div>
                
                <div class="board" id="gameBoard"></div>
                
                <div>
                    <div>Вы играете за: <span id="playerSymbol" style="font-weight: bold;"></span></div>
                    <div>Сейчас ходит: <span id="currentTurn" style="font-weight: bold;"></span></div>
                </div>
                
                <button onclick="restartGame()">Новая игра</button>
            </div>
        </div>

        <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
        <script>
            const socket = io();
            let currentGameId = '';
            let playerSymbol = '';
            let isMyTurn = false;
            let currentTurn = 'X';

            function connectToGame() {
                const gameId = document.getElementById('gameIdInput').value.trim() || 'default';
                currentGameId = gameId;
                
                socket.emit('join', { game_id: gameId });
            }

            function initBoard(boardData) {
                const board = document.getElementById('gameBoard');
                board.innerHTML = '';
                
                for (let i = 0; i < 3; i++) {
                    for (let j = 0; j < 3; j++) {
                        const cell = document.createElement('button');
                        cell.className = 'cell';
                        cell.dataset.row = i;
                        cell.dataset.col = j;
                        cell.textContent = boardData[i][j] || '';
                        cell.disabled = !isMyTurn || boardData[i][j] !== '';
                        
                        if (cell.textContent === 'X') cell.classList.add('x');
                        if (cell.textContent === 'O') cell.classList.add('o');
                        
                        cell.addEventListener('click', () => makeMove(i, j));
                        board.appendChild(cell);
                    }
                }
            }

            function makeMove(row, col) {
                if (!isMyTurn) return;
                socket.emit('move', { row, col, game_id: currentGameId });
            }

            function restartGame() {
                socket.emit('restart', { game_id: currentGameId });
            }

            // Socket events
            socket.on('connect', () => {
                updateConnectionStatus('Подключение установлено', 'playing');
            });

            socket.on('game_start', (data) => {
                playerSymbol = data.symbol;
                isMyTurn = playerSymbol === 'X';
                currentTurn = 'X';
                
                document.getElementById('connectionSection').classList.add('hidden');
                document.getElementById('gameSection').classList.remove('hidden');
                
                initBoard(data.board);
                updateGameStatus(isMyTurn ? 'Ваш ход! Ходите крестиками (X)' : 'Ход соперника...');
                updateTurnDisplay();
            });

            socket.on('board_update', (data) => {
                updateBoard(data.board);
                currentTurn = data.turn;
                isMyTurn = playerSymbol === currentTurn;
                updateGameStatus(isMyTurn ? 'Ваш ход!' : 'Ход соперника...');
                updateTurnDisplay();
            });

            socket.on('game_over', (data) => {
                if (data.winner === 'draw') {
                    updateGameStatus('Ничья!', 'waiting');
                } else {
                    const isWinner = data.winner === playerSymbol;
                    updateGameStatus(isWinner ? 'Вы победили! 🎉' : 'Вы проиграли!', 
                                   isWinner ? 'winner' : 'waiting');
                }
            });

            socket.on('error', (data) => {
                updateGameStatus('Ошибка: ' + data.message, 'waiting');
            });

            function updateBoard(boardData) {
                const cells = document.querySelectorAll('.cell');
                cells.forEach(cell => {
                    const row = parseInt(cell.dataset.row);
                    const col = parseInt(cell.dataset.col);
                    const symbol = boardData[row][col];
                    
                    cell.textContent = symbol || '';
                    cell.disabled = !isMyTurn || symbol !== '';
                    
                    cell.classList.remove('x', 'o');
                    if (symbol === 'X') cell.classList.add('x');
                    if (symbol === 'O') cell.classList.add('o');
                });
            }

            function updateConnectionStatus(message, type) {
                const element = document.getElementById('connectionStatus');
                element.textContent = message;
                element.className = `status ${type}`;
            }

            function updateGameStatus(message, type = '') {
                const element = document.getElementById('gameStatus');
                element.textContent = message;
                element.className = type ? `status ${type}` : 'status';
            }

            function updateTurnDisplay() {
                document.getElementById('playerSymbol').textContent = playerSymbol;
                document.getElementById('currentTurn').textContent = currentTurn;
                document.getElementById('currentTurn').style.color = currentTurn === 'X' ? '#e74c3c' : '#3498db';
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/health')
def health():
    return {
        'status': 'healthy', 
        'active_games': len(games),
        'total_players': len(players)
    }

# WebSocket handlers
@socketio.on('connect')
def handle_connect():
    logger.info(f'Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to game server'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected: {request.sid}')
    if request.sid in players:
        game_id = players[request.sid]
        if game_id in games:
            game = games[game_id]
            # Удаляем игрока из игры
            if game['players']['X'] == request.sid:
                game['players']['X'] = None
            elif game['players']['O'] == request.sid:
                game['players']['O'] = None
            
            # Если оба игрока отключились, удаляем игру
            if game['players']['X'] is None and game['players']['O'] is None:
                del games[game_id]
        
        del players[request.sid]

@socketio.on('join')
def handle_join(data):
    game_id = data.get('game_id', 'default')
    logger.info(f'Player {request.sid} joining game {game_id}')
    
    if game_id not in games:
        # Создаем новую игру
        games[game_id] = {
            'board': [['', '', ''] for _ in range(3)],
            'players': {'X': request.sid, 'O': None},
            'current_turn': 'X',
            'status': 'waiting'
        }
        players[request.sid] = game_id
        emit('waiting', {'message': 'Ожидаем второго игрока...'})
    else:
        game = games[game_id]
        if game['players']['O'] is None:
            # Второй игрок присоединяется
            game['players']['O'] = request.sid
            game['status'] = 'playing'
            players[request.sid] = game_id
            
            # Уведомляем обоих игроков о начале игры
            emit('game_start', {
                'symbol': 'O',
                'board': game['board']
            }, room=request.sid)
            
            emit('game_start', {
                'symbol': 'X', 
                'board': game['board']
            }, room=game['players']['X'])
            
            emit('board_update', {
                'board': game['board'],
                'turn': 'X'
            }, room=game_id)
            
            logger.info(f'Game {game_id} started')
        else:
            emit('error', {'message': 'Комната заполнена'})

@socketio.on('move')
def handle_move(data):
    game_id = data.get('game_id')
    row = data.get('row')
    col = data.get('col')
    
    if not game_id or game_id not in games:
        emit('error', {'message': 'Игра не найдена'})
        return
    
    game = games[game_id]
    player_sid = request.sid
    
    # Проверяем, чей ход
    current_symbol = game['current_turn']
    if game['players'][current_symbol] != player_sid:
        emit('error', {'message': 'Не ваш ход'})
        return
    
    # Проверяем, что клетка свободна
    if game['board'][row][col] != '':
        emit('error', {'message': 'Клетка уже занята'})
        return
    
    # Делаем ход
    game['board'][row][col] = current_symbol
    
    # Проверяем победу
    winner = check_winner(game['board'])
    if winner:
        game['status'] = 'finished'
        emit('game_over', {'winner': winner}, room=game_id)
        # Авторестарт через 3 секунды
        socketio.sleep(3)
        reset_game(game_id)
        emit('game_restart', {'board': game['board']}, room=game_id)
    elif is_board_full(game['board']):
        emit('game_over', {'winner': 'draw'}, room=game_id)
        socketio.sleep(3)
        reset_game(game_id)
        emit('game_restart', {'board': game['board']}, room=game_id)
    else:
        # Меняем ход
        game['current_turn'] = 'O' if current_symbol == 'X' else 'X'
        emit('board_update', {
            'board': game['board'],
            'turn': game['current_turn']
        }, room=game_id)

@socketio.on('restart')
def handle_restart(data):
    game_id = data.get('game_id')
    if game_id in games:
        reset_game(game_id)
        emit('game_restart', {'board': games[game_id]['board']}, room=game_id)

def check_winner(board):
    # Проверка строк
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != '':
            return board[i][0]
    
    # Проверка столбцов
    for i in range(3):
        if board[0][i] == board[1][i] == board[2][i] != '':
            return board[0][i]
    
    # Проверка диагоналей
    if board[0][0] == board[1][1] == board[2][2] != '':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] != '':
        return board[0][2]
    
    return None

def is_board_full(board):
    return all(cell != '' for row in board for cell in row)

def reset_game(game_id):
    if game_id in games:
        games[game_id]['board'] = [['', '', ''] for _ in range(3)]
        games[game_id]['current_turn'] = 'X'
        games[game_id]['status'] = 'playing'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Сервер крестиков-ноликов запускается на порту {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
