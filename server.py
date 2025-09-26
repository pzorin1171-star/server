from flask import Flask, send_from_directory
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
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>🎮 Крестики-нолики</h1>
        <p>Сервер работает успешно!</p>
        <div id="status">Статус: ✅ Работает</div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'healthy', 'message': 'Server is running'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
