from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tic-tac-toe-final-version'

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
        <meta charset="UTF-8">
        <style>
            body { font-family: Arial; text-align: center; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { background: white; max-width: 400px; margin: 0 auto; padding: 20px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
            h1 { color: #333; margin-bottom: 20px; }
            .board { display: grid; grid-template-columns: repeat(3, 100px); gap: 5px; margin: 20px auto; justify-content: center; }
            .cell { width: 100px; height: 100px; border: 3px solid #667eea; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 40px; font-weight: bold; cursor: pointer; background: #f8f9fa; transition: all 0.3s; }
            .cell:hover { background: #e9ecef; transform: scale(1.05); }
            .cell.x { color: #e74c3c; }
            .cell.o { color: #3498db; }
            .cell:disabled { cursor: not-allowed; transform: none; }
            .cell:disabled:hover { background: #f8f9fa; }
            .status { margin: 15px 0; padding: 15px; border-radius: 10px; font-size: 16px; font-weight: bold; }
            .waiting { background: #fff3cd; color: #856404; }
            .ready { background: #d4edda; color: #155724; }
            .my-turn { background: #cce5ff; color: #004085; }
            input, button { padding: 12px; margin: 5px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
            button { background: #667eea; color: white; cursor: pointer; transition: background 0.3s; }
            button:hover { background: #5a6fd8; }
            button:disabled { background: #ccc; cursor: not-allowed; }
            .game-info { margin: 15px 0; font-size: 18px; }
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎮 Крестики-нолики</h1>
            
            <div id="connectSection">
                <div>
                    <input type="text" id="roomInput" value="game1" placeholder="Название комнаты">
                    <button onclick="connectToGame()">Присоединиться</button>
                </div>
                <div id="status" class="status waiting">Введите название комнаты и нажмите "Присоединиться"</div>
            </div>
            
            <div id="gameSection" class="hidden">
                <div class="game-info">
                    Вы играете за: <span id="playerSymbol" style="font-weight: bold;">-</span>
                </div>
                <div class="game-info">
                    Статус: <span id="gameStatus">Ожидаем второго игрока...</span>
                </div>
                
                <div class="board" id="gameBoard"></div>
                
                <div class="game-info">
                    Сейчас ходит: <span id="turnInfo">-</span>
                </div>
                
                <button onclick="resetGame()" id="resetBtn">Новая игра</button>
                <button onclick="leaveGame()" style="background: #e74c3c;">Выйти из игры</button>
            </div>
        </div>

        <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
        <script>
            let socket = null;
            let currentRoom = '';
            let mySymbol = '';
            let isMyTurn = false;
            let gameActive = false;
            let board = ['', '', '', '', '', '', '', '', ''];
            
            function connectToGame() {
                currentRoom = document.getElementById('roomInput').value.trim() || 'default';
                
                if (socket) {
                    socket.disconnect();
                }
                
                socket = io();
                
                socket.on('connect', function() {
                    updateStatus('Подключено к серверу!', 'ready');
                    socket.emit('join', { room: currentRoom });
                });
                
                socket.on('joined', function(data) {
                    mySymbol = data.symbol;
                    updateStatus(data.message, 'ready');
                    document.getElementById('playerSymbol').textContent = mySymbol;
                    document.getElementById('playerSymbol').style.color = mySymbol === 'X' ? '#e74c3c' : '#3498db';
                    
                    document.getElementById('connectSection').classList.add('hidden');
                    document.getElementById('gameSection').classList.remove('hidden');
                    
                    createBoard();
                });
                
                socket.on('game_start', function(data) {
                    gameActive = true;
                    board = data.board;
                    isMyTurn = data.currentPlayer === mySymbol;
                    updateBoard();
                    updateGameStatus();
                });
                
                socket.on('move_made', function(data) {
                    board[data.index] = data.symbol;
                    isMyTurn = data.nextPlayer === mySymbol;
                    updateBoard();
                    updateGameStatus();
                });
                
                socket.on('game_over', function(data) {
                    gameActive = false;
                    if (data.winner === 'draw') {
                        updateStatus('Ничья! Начинаем новую игру через 3 секунды...', 'waiting');
                    } else {
                        const won = data.winner === mySymbol;
                        updateStatus(won ? 'Вы победили! 🎉' : 'Вы проиграли!', won ? 'ready' : 'waiting');
                    }
                });
                
                socket.on('player_joined', function(data) {
                    updateStatus('Второй игрок присоединился! Игра начинается!', 'ready');
                });
                
                socket.on('player_left', function(data) {
                    gameActive = false;
                    updateStatus('Соперник покинул игру. Ожидаем нового игрока...', 'waiting');
                });
                
                socket.on('error', function(data) {
                    updateStatus('Ошибка: ' + data.message, 'waiting');
                });
            }
            
            function createBoard() {
                const boardElement = document.getElementById('gameBoard');
                boardElement.innerHTML = '';
                
                for (let i = 0; i < 9; i++) {
                    const cell = document.createElement('div');
                    cell.className = 'cell';
                    cell.onclick = () => makeMove(i);
                    boardElement.appendChild(cell);
                }
                updateBoard();
            }
            
            function makeMove(index) {
                if (gameActive && isMyTurn && board[index] === '') {
                    socket.emit('move', {
                        room: currentRoom,
                        index: index,
                        symbol: mySymbol
                    });
                }
            }
            
            function updateBoard() {
                const cells = document.querySelectorAll('.cell');
                cells.forEach((cell, index) => {
                    cell.textContent = board[index] || '';
                    cell.className = 'cell ' + (board[index] || '');
                    
                    if (board[index] === 'X') {
                        cell.classList.add('x');
                    } else if (board[index] === 'O') {
                        cell.classList.add('o');
                    }
                    
                    cell.style.cursor = (gameActive && isMyTurn && !board[index]) ? 'pointer' : 'default';
                });
            }
            
            function updateGameStatus() {
                const statusElement = document.getElementById('gameStatus');
                const turnElement = document.getElementById('turnInfo');
                
                if (gameActive) {
                    if (isMyTurn) {
                        statusElement.textContent = 'Ваш ход!';
                        statusElement.className = 'status my-turn';
                        turnElement.textContent = mySymbol;
                        turnElement.style.color = mySymbol === 'X' ? '#e74c3c' : '#3498db';
                    } else {
                        statusElement.textContent = 'Ход соперника...';
                        statusElement.className = 'status waiting';
                        const opponentSymbol = mySymbol === 'X' ? 'O' : 'X';
                        turnElement.textContent = opponentSymbol;
                        turnElement.style.color = opponentSymbol === 'X' ? '#e74c3c' : '#3498db';
                    }
                }
            }
            
            function updateStatus(message, type) {
                const statusElement = document.getElementById('status');
                statusElement.textContent = message;
                statusElement.className = 'status ' + type;
            }
            
            function resetGame() {
                if (socket) {
                    socket.emit('reset', { room: currentRoom });
                }
            }
            
            function leaveGame() {
                if (socket) {
                    socket.emit('leave', { room: currentRoom });
                    socket.disconnect();
                }
                document.getElementById('gameSection').classList.add('hidden');
                document.getElementById('connectSection').classList.remove('hidden');
                updateStatus('Введите название комнаты', 'waiting');
            }
            
            // Автоподключение при загрузке, если есть параметр room в URL
            window.addEventListener('load', function() {
                const urlParams = new URLSearchParams(window.location.search);
                const roomFromUrl = urlParams.get('room');
                if (roomFromUrl) {
                    document.getElementById('roomInput').value = roomFromUrl;
                    connectToGame();
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'healthy', 'active_games': len(games)}

@socketio.on('connect')
def handle_connect():
    print(f'👉 Клиент подключился: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'👋 Клиент отключился: {request.sid}')
    # Удаляем игрока из всех комнат при отключении
    for room, game in games.items():
        if game['players']['X'] == request.sid:
            game['players']['X'] = None
            if game['players']['O']:
                emit('player_left', room=room)
        elif game['players']['O'] == request.sid:
            game['players']['O'] = None
            if game['players']['X']:
                emit('player_left', room=room)

@socketio.on('join')
def handle_join(data):
    room = data.get('room', 'default')
    join_room(room)
    
    if room not in games:
        # Создаем новую игру
        games[room] = {
            'players': {'X': request.sid, 'O': None},
            'board': ['', '', '', '', '', '', '', '', ''],
            'current_player': 'X',
            'game_active': False
        }
        emit('joined', {
            'symbol': 'X',
            'message': 'Ожидаем второго игрока...'
        })
        print(f'🎮 Создана новая игра в комнате: {room}')
        
    else:
        game = games[room]
        if game['players']['O'] is None and game['players']['X'] != request.sid:
            # Второй игрок присоединяется
            game['players']['O'] = request.sid
            game['game_active'] = True
            
            emit('joined', {
                'symbol': 'O',
                'message': 'Вы играете за O'
            })
            
            # Уведомляем первого игрока
            emit('player_joined', room=game['players']['X'])
            
            # Начинаем игру для обоих игроков
            emit('game_start', {
                'board': game['board'],
                'currentPlayer': 'X'
            }, room=room)
            
            print(f'🎯 Игра началась в комнате: {room} (2 игрока)')
            
        else:
            # Игрок уже в комнате или комната заполнена
            if game['players']['X'] == request.sid or game['players']['O'] == request.sid:
                # Игрок переподключился
                symbol = 'X' if game['players']['X'] == request.sid else 'O'
                emit('joined', {
                    'symbol': symbol,
                    'message': 'Переподключение к игре'
                })
                if game['game_active']:
                    emit('game_start', {
                        'board': game['board'],
                        'currentPlayer': game['current_player']
                    })
            else:
                emit('error', {'message': 'Комната заполнена'})

@socketio.on('move')
def handle_move(data):
    room = data.get('room')
    index = data.get('index')
    symbol = data.get('symbol')
    
    if room not in games:
        return
    
    game = games[room]
    
    # Проверяем валидность хода
    if (not game['game_active'] or
        game['current_player'] != symbol or
        index < 0 or index > 8 or
        game['board'][index] != ''):
        return
    
    # Проверяем, что ход делает правильный игрок
    if (symbol == 'X' and game['players']['X'] != request.sid) or \
       (symbol == 'O' and game['players']['O'] != request.sid):
        return
    
    # Делаем ход
    game['board'][index] = symbol
    
    # Проверяем победу
    winner = check_winner(game['board'])
    if winner:
        game['game_active'] = False
        emit('game_over', {'winner': winner}, room=room)
        # Авторестарт через 3 секунды
        socketio.sleep(3)
        handle_reset({'room': room})
    elif all(cell != '' for cell in game['board']):
        game['game_active'] = False
        emit('game_over', {'winner': 'draw'}, room=room)
        socketio.sleep(3)
        handle_reset({'room': room})
    else:
        # Меняем ход
        game['current_player'] = 'O' if symbol == 'X' else 'X'
        emit('move_made', {
            'index': index,
            'symbol': symbol,
            'nextPlayer': game['current_player']
        }, room=room)

@socketio.on('reset')
def handle_reset(data):
    room = data.get('room')
    if room in games and games[room]['game_active'] == False:
        games[room]['board'] = ['', '', '', '', '', '', '', '', '']
        games[room]['current_player'] = 'X'
        games[room]['game_active'] = True
        
        emit('game_start', {
            'board': games[room]['board'],
            'currentPlayer': 'X'
        }, room=room)

@socketio.on('leave')
def handle_leave(data):
    room = data.get('room')
    leave_room(room)
    
    if room in games:
        game = games[room]
        if game['players']['X'] == request.sid:
            game['players']['X'] = None
        elif game['players']['O'] == request.sid:
            game['players']['O'] = None
        
        # Если оба игрока вышли, удаляем игру
        if not game['players']['X'] and not game['players']['O']:
            del games[room]

def check_winner(board):
    # Выигрышные комбинации
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Горизонтальные
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Вертикальные
        [0, 4, 8], [2, 4, 6]              # Диагональные
    ]
    
    for a, b, c in lines:
        if board[a] and board[a] == board[b] and board[a] == board[c]:
            return board[a]
    return None

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Сервер крестиков-ноликов запущен на порту {port}")
    print(f"🎮 Доступен по адресу: http://localhost:{port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
