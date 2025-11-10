from flask import Flask, jsonify, render_template, request
from backend.game_manager import GameManager

app = Flask(__name__)

# Gets rid of any scope problems
class GameState:
    def __init__(self):
        self._game = None
        self._has_started = False
    
    def has_started(self):
        return self._has_started

    def start(self):
        self._has_started = True

    def get_game(self):
        return self._game

    def set_game(self, game):
        self._game = game

game = GameState()

@app.route("/")
def home():
    return render_template("index.html")

# Solo mode
@app.get("/solo")
def get_board():
    return render_template("solo.html")

@app.post("/start")
def start():
    if not game.has_started():
        game.start()

    game.set_game(GameManager(6, 7))
    return game.get_game().to_dict()

@app.post("/move/<direction>")
def make_move(direction):
    if not game.has_started():
        return jsonify({"error": "No active game"}), 400

    game.get_game().move(direction)
    return game.get_game().to_dict()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
