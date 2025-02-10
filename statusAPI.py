import socket
from flask import Flask, jsonify, request

app = Flask(__name__)

class checkSerwer:
    def __init__(self, address: str, port: int = 22003):
        self.address = address
        self.port = port
        self.response = None
        self.returns = {}
        self.polacz(address, port)

    def przetworz(self, start):
        start_end = start + 1
        length = ord(self.response[start:start_end]) - 1
        value = self.response[start_end:start_end + length]
        return start_end + length, value.decode('utf-8')

    def wyswietl(self):
        params = ('game', 'port', 'name', 'gamemode', 'map', 'version', 'somewhat', 'players', 'maxplayers')
        start = 4
        for param in params:
            start, value = self.przetworz(start)
            setattr(self, param, value)
        self.returns = {
            "game": self.game,
            "port": self.port,
            "name": self.name,
            "gamemode": self.gamemode,
            "map": self.map,
            "version": self.version,
            "somewhat": self.somewhat,
            "players": self.players,
            "maxplayers": self.maxplayers
        }

    def polacz(self, address, port):
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        serversocket.settimeout(5) 
        serversocket.connect((address, port + 123))
        serversocket.send(b"s")
        self.response = serversocket.recv(16384)  
        self.wyswietl()
        serversocket.close()

@app.route('/server-status', methods=['GET'])
def server_status():
    address = request.args.get('address', '137.74.4.38') # ip serwera
    port = int(request.args.get('port', 22003))

    try:
        server = checkSerwer(address, port)
        return jsonify(server.returns), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
