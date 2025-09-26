from flask import Flask
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-secret-key'

# Упрощенная инициализация SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Хранилище игр
games = {}

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Крестики-нолики MULTIPLAYER</title>
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial; text-align: center; margin: 20px; }
            .container { max-width: 500px; margin: 0 auto; }
            .board { display: grid; grid-template-columns: repeat(3, 80px); gap: 5px; margin: 20px auto; justify-content: center; }
            .cell { width: 80px; height: 80px; border: 2px solid #333; display: flex; align-items: center; justify-content: center; font-size: 24px; cursor: pointer; }
            .cell.x { color: red; }
            .cell.o { color: blue; }
            .status { margin: 10px; padding: 10px; border-radius: 5px; }
            .online { background: #d4ffd4; }
            .offline { background: #ffd4d4; }
            input, button { padding: 8px; margin: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 Крестики-нолики ONLINE</h1>
            <div id="status" class="status offline">Отключено</div>
            
            <div>
                <input type="text" id="gameId" value="room1" placeholder="ID комнаты">
                <button onclick="connectGame()">Присоединиться</button>
            </div>
            
            <div id="gameInfo" style="display:none">
                <div>Вы играете за: <span id="mySymbol" style="font-weight:bold">-</span></div>
                <div>Сейчас ходит: <span id="turnInfo">-</span></div>
            </div>
            
            <div class="board" id="board"></div>
            <button onclick="resetGame()" style="display:none" id="resetBtn">Новая игра</button>
        </div>

        <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
        <script>
            let socket = null;
            let currentGameId = '';
            let mySymbol = '';
            let isMyTurn = false;
            let board = ['','','','','','','','',''];
            
            function createBoard() {
                const boardEl = document.getElementById('board');
                boardEl.innerHTML = '';
                for (let i = 0; i < 9; i++) {
                    const cell = document.createElement('div');
                    cell.className = 'cell';
                    cell.onclick = () => makeMove(i);
                    boardEl.appendChild(cell);
                }
                updateBoard();
            }
            
            function connectGame() {
                currentGameId = document.getElementById('gameId').value || 'default';
                
                socket = io();
                
                socket.on('connect', () => {
                    document.getElementById('status').textContent = 'Подключено';
                    document.getElementById('status').className = 'status online';
                    socket.emit('join_game', {gameId: currentGameId});
                });
                
                socket.on('player_assigned', (data) => {
                    mySymbol = data.symbol;
                    document.getElementById('mySymbol').textContent = mySymbol;
                    document.getElementById('mySymbol').style.color = mySymbol === 'X' ? 'red' : 'blue';
                    document.getElementById('gameInfo').style.display = 'block';
                });
                
                socket.on('game_state', (data) => {
                    board = data.board;
                    isMyTurn = data.currentTurn === mySymbol;
                    updateBoard();
                    updateTurnInfo();
                });
                
                socket.on('move_made', (data) => {
                    board[data.position] = data.symbol;
                    isMyTurn = data.nextTurn === mySymbol;
                    updateBoard();
                    updateTurnInfo();
                });
                
                socket.on('game_over', (data) => {
                    if (data.winner === 'draw') {
                        alert('Ничья!');
                    } else {
                        alert(data.winner === mySymbol ? 'Вы победили!' : 'Вы проиграли!');
                    }
                    document.getElementById('resetBtn').style.display = 'block';
                });
                
                socket.on('error', (data) => {
                    alert('Ошибка: ' + data.message);
                });
                
                createBoard();
            }
            
            function makeMove(position) {
                if (isMyTurn && board[position] === '' && socket) {
                    socket.emit('make_move', {
                        gameId: currentGameId,
                        position: position,
                        symbol: mySymbol
                    });
                }
            }
            
            function updateBoard() {
                const cells = document.querySelectorAll('.cell');
                cells.forEach((cell, i) => {
                    cell.textContent = board[i];
                    cell.className = 'cell ' + board[i];
                    cell.style.background = board[i] ? '#f0f0f0' : '';
                    cell.style.cursor = (isMyTurn && !board[i]) ? 'pointer' : 'default';
                });
            }
            
            function updateTurnInfo() {
                const turnEl = document.getElementById('turnInfo');
                if (isMyTurn) {
                    turnEl.innerHTML = '<span style="color:green">ВЫ</span>';
                } else {
                    turnEl.innerHTML = '<span style="color:red">Соперник</span>';
                }
            }
            
            function resetGame() {
                if (socket) {
                    socket.emit('reset_game', {gameId: currentGameId});
                    document.getElementById('resetBtn').style.display = 'none';
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'ok', 'active_games': len(games)}

# SocketIO handlers
@socketio.on('connect')
def handle_connect():
    print('Клиент подключен')

@socketio.on('disconnect')
def handle_disconnect():
    print('Клиент отключен')

@socketio.on('join_game')
def handle_join_game(data):
    game_id = data.get('gameId', 'default')
    
    if game_id not in games:
        # Создаем новую игру
        games[game_id] = {
            'board': ['','','','','','','','',''],
            'players': {'X': None, 'O': None},
            'current_turn': 'X',
            'move_count': 0
        }
    
    game = games[game_id]
    
    # Назначаем игрока
    if game['players']['X'] is None:
        game['players']['X'] = request.sid
        symbol = 'X'
    elif game['players']['O'] is None:
        game['players']['O'] = request.sid
        symbol = 'O'
    else:
        # Комната заполнена
        emit('error', {'message': 'Комната заполнена'})
        return
    
    # Отправляем данные игроку
    emit('player_assigned', {'symbol': symbol})
    emit('game_state', {
        'board': game['board'],
        'currentTurn': game['current_turn']
    })
    
    # Если оба игрока подключены, начинаем игру
    if game['players']['X'] and game['players']['O']:
        socketio.emit('game_state', {
            'board': game['board'],
            'currentTurn': game['current_turn']
        }, room=game_id)

@socketio.on('make_move')
def handle_make_move(data):
    game_id = data.get('gameId')
    position = data.get('position')
    symbol = data.get('symbol')
    
    if game_id not in games:
        return
    
    game = games[game_id]
    
    # Проверяем валидность хода
    if (game['current_turn'] != symbol or 
        game['players'][symbol] != request.sid or
        position < 0 or position > 8 or
        game['board'][position] != ''):
        return
    
    # Выполняем ход
    game['board'][position] = symbol
    game['move_count'] += 1
    
    # Проверяем победу
    winner = check_winner(game['board'])
    if winner:
        socketio.emit('game_over', {'winner': winner}, room=game_id)
    elif game['move_count'] >= 9:
        socketio.emit('game_over', {'winner': 'draw'}, room=game_id)
    else:
        # Меняем ход
        game['current_turn'] = 'O' if symbol == 'X' else 'X'
        socketio.emit('move_made', {
            'position': position,
            'symbol': symbol,
            'nextTurn': game['current_turn']
        }, room=game_id)

@socketio.on('reset_game')
def handle_reset_game(data):
    game_id = data.get('gameId')
    if game_id in games:
        games[game_id] = {
            'board': ['','','','','','','','',''],
            'players': games[game_id]['players'],  # Сохраняем игроков
            'current_turn': 'X',
            'move_count': 0
        }
        socketio.emit('game_state', {
            'board': games[game_id]['board'],
            'currentTurn': 'X'
        }, room=game_id)

def check_winner(board):
    lines = [
        [0,1,2],[3,4,5],[6,7,8],  # rows
        [0,3,6],[1,4,7],[2,5,8],  # columns
        [0,4,8],[2,4,6]           # diagonals
    ]
    
    for a, b, c in lines:
        if board[a] and board[a] == board[b] and board[a] == board[c]:
            return board[a]
    return None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"✅ Мультиплеер сервер запущен на порту {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
