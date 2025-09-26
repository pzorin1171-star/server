from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Крестики-нолики</title>
        <style>
            body { font-family: Arial; text-align: center; margin: 50px; }
            .board { display: inline-grid; grid-template-columns: repeat(3, 100px); gap: 5px; margin: 20px; }
            .cell { width: 100px; height: 100px; border: 2px solid #333; font-size: 40px; cursor: pointer; }
            .cell.x { color: red; }
            .cell.o { color: blue; }
        </style>
    </head>
    <body>
        <h1>🎮 Крестики-нолики (Оффлайн версия)</h1>
        <div class="board" id="board"></div>
        <div id="status">Ход: <span id="turn">X</span></div>
        <button onclick="resetGame()">Новая игра</button>
        
        <script>
            let board = Array(9).fill('');
            let currentPlayer = 'X';
            
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
            
            function makeMove(index) {
                if (board[index] === '' && !checkWinner()) {
                    board[index] = currentPlayer;
                    currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
                    updateBoard();
                    
                    const winner = checkWinner();
                    if (winner) {
                        document.getElementById('status').innerHTML = `Победитель: <span style="color: ${winner === 'X' ? 'red' : 'blue'}">${winner}</span>`;
                    } else if (board.every(cell => cell !== '')) {
                        document.getElementById('status').textContent = 'Ничья!';
                    } else {
                        document.getElementById('status').innerHTML = `Ход: <span style="color: ${currentPlayer === 'X' ? 'red' : 'blue'}">${currentPlayer}</span>`;
                    }
                }
            }
            
            function updateBoard() {
                const cells = document.querySelectorAll('.cell');
                cells.forEach((cell, index) => {
                    cell.textContent = board[index];
                    cell.className = `cell ${board[index]}`;
                });
            }
            
            function checkWinner() {
                const lines = [
                    [0,1,2],[3,4,5],[6,7,8], // rows
                    [0,3,6],[1,4,7],[2,5,8], // columns
                    [0,4,8],[2,4,6] // diagonals
                ];
                
                for (let [a,b,c] of lines) {
                    if (board[a] && board[a] === board[b] && board[a] === board[c]) {
                        return board[a];
                    }
                }
                return null;
            }
            
            function resetGame() {
                board = Array(9).fill('');
                currentPlayer = 'X';
                document.getElementById('status').innerHTML = 'Ход: <span style="color: red">X</span>';
                updateBoard();
            }
            
            // Initialize game
            createBoard();
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'Server is running'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
