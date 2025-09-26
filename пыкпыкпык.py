from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
CORS(app)  # Разрешаем запросы с любого origin для простоты

# Для продакшена важно указать конкретные домены
# CORS(app, origins=[os.environ.get('FRONTEND_URL', 'https://your-frontend.onrender.com')])

socketio = SocketIO(app, cors_allowed_origins="*")

# Состояние игры
games = {}
current_players = {}

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    print(f'Client disconnected: {sid}')
    
    if sid in current_players:
        game_id = current_players[sid]
        if game_id in games:
            # Уведомляем другого игрока о дисконнекте
            players = games[game_id]['players']
            opponent = players[1] if players[0] == sid else players[0]
            if opponent:
                emit('opponent_disconnected', room=opponent)
            
            del games[game_id]
        del current_players[sid]

@socketio.on('join')
def handle_join(data):
    sid = request.sid
    game_id = data.get('game_id', 'default')
    current_players[sid] = game_id
    
    if game_id not in games:
        games[game_id] = {
            'board': [['', '', ''] for _ in range(3)],
            'players': [sid, None],
            'current_turn': 'X',
            'spectators': []
        }
        emit('waiting', {'game_id': game_id}, room=sid)
        print(f'Game {game_id} created by {sid}')
    else:
        game = games[game_id]
        if game['players'][1] is None:
            game['players'][1] = sid
            emit('game_start', {'symbol': 'O', 'board': game['board']}, room=sid)
            emit('game_start', {'symbol': 'X', 'board': game['board']}, room=game['players'][0])
            emit('turn_update', {'turn': 'X'}, room=game_id)
            print(f'Game {game_id} started with two players')
        else:
            # Можно добавить режим наблюдателя
            game['spectators'].append(sid)
            emit('spectator_mode', {'board': game['board'], 'turn': game['current_turn']}, room=sid)

@socketio.on('move')
def handle_move(data):
    sid = request.sid
    game_id = current_players.get(sid)
    
    if not game_id or game_id not in games:
        emit('error', {'message': 'Game not found'}, room=sid)
        return
        
    game = games[game_id]
    row = data.get('row')
    col = data.get('col')
    
    # Проверка валидности хода
    if row is None or col is None or row not in [0, 1, 2] or col not in [0, 1, 2]:
        emit('error', {'message': 'Invalid move coordinates'}, room=sid)
        return
    
    # Проверка, что клетка свободна
    if game['board'][row][col] != '':
        emit('error', {'message': 'Cell already occupied'}, room=sid)
        return
    
    # Проверка очереди хода
    current_player_index = 0 if game['current_turn'] == 'X' else 1
    if game['players'][current_player_index] != sid:
        emit('error', {'message': 'Not your turn'}, room=sid)
        return
    
    # Выполнение хода
    game['board'][row][col] = game['current_turn']
    
    # Проверка победы
    winner = check_winner(game['board'])
    if winner:
        emit('game_over', {
            'winner': winner,
            'winning_cells': get_winning_cells(game['board'])
        }, room=game_id)
        # Автоматический рестарт через 5 секунд
        socketio.sleep(5)
        reset_game(game_id)
        emit('game_restarted', {'board': games[game_id]['board'], 'turn': 'X'}, room=game_id)
    elif is_board_full(game['board']):
        emit('game_over', {'winner': 'draw'}, room=game_id)
        socketio.sleep(5)
        reset_game(game_id)
        emit('game_restarted', {'board': games[game_id]['board'], 'turn': 'X'}, room=game_id)
    else:
        # Смена хода
        game['current_turn'] = 'O' if game['current_turn'] == 'X' else 'X'
        emit('move_made', {
            'row': row,
            'col': col,
            'symbol': data['symbol'],
            'turn': game['current_turn'],
            'board': game['board']
        }, room=game_id)

@socketio.on('restart_game')
def handle_restart():
    sid = request.sid
    game_id = current_players.get(sid)
    
    if game_id and game_id in games:
        reset_game(game_id)
        emit('game_restarted', {
            'board': games[game_id]['board'],
            'turn': games[game_id]['current_turn']
        }, room=game_id)

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

def get_winning_cells(board):
    # Проверка строк
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] != '':
            return [[i, 0], [i, 1], [i, 2]]
    
    # Проверка столбцов
    for i in range(3):
        if board[0][i] == board[1][i] == board[2][i] != '':
            return [[0, i], [1, i], [2, i]]
    
    # Проверка диагоналей
    if board[0][0] == board[1][1] == board[2][2] != '':
        return [[0, 0], [1, 1], [2, 2]]
    if board[0][2] == board[1][1] == board[2][0] != '':
        return [[0, 2], [1, 1], [2, 0]]
    
    return []

def is_board_full(board):
    return all(cell != '' for row in board for cell in row)

def reset_game(game_id):
    if game_id in games:
        games[game_id]['board'] = [['', '', ''] for _ in range(3)]
        games[game_id]['current_turn'] = 'X'

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'active_games': len(games)}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting server on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
