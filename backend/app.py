from flask import Flask, jsonify, render_template, request, url_for, redirect, session, abort
from datetime import timedelta, datetime
from random import random
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
from backend.game_manager import GameManager

app = Flask(__name__)

# This limit may get capped in some browsers
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365*2)

# Use SQLite
from flask_sqlalchemy import SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///info.db"
db = SQLAlchemy(app) 

def generate_user_id() -> str:
    return str(uuid.uuid4())

# session expires in 365*2 days (about 2 years)
class User(db.Model):
    user_id = db.Column(db.String(36), primary_key=True)  # UUID
    num_wins = db.Column(db.Integer, default=0, nullable=False)
    num_losses = db.Column(db.Integer, default=0, nullable=False)
    num_abandoned_games = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

# Should be run periodically
def cleanup_expired_sessions():
    now = datetime.utcnow()
    User.query.filter(User.created_at + timedelta(days=365*2) < now).delete()
    db.session.commit()

# Use client-side Flask sessions for non-sensitive data
# A session should store data for id, current game, and statistics (wins/losses/abandoned games, and maybe time/moves taken)
# Generate a secret key with the command $ python -c 'import secrets; print(secrets.token_hex())'
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")

def dict_to_game(game_dict):
    grid = game_dict["grid"]
    round_num = game_dict["round"]
    state = game_dict["state"]
    cur_game = GameManager(6, 7)
    cur_game.get_game().set_game(grid)
    cur_game.set_round(round_num)
    cur_game.set_state(state)
    cur_game.update_valid_moves()
    return cur_game

# session is permanent unless it expires, the user deletes cookie manually, or the server restarts 
@app.before_request
def ensure_session():
    if "user_id" not in session:
        session["user_id"] = generate_user_id()
        session["current_solo_game"] = GameManager(6, 7).to_dict()
        session.permanent = True 
        db.session.add(User(user_id=session["user_id"]))
        db.session.commit()
    
    if random() < 0.001:
        cleanup_expired_sessions()

@app.route("/", methods=["GET"])
def index():
    user_id = session["user_id"]
    user = User.query.get_or_404(user_id)
    wins = user.num_wins
    losses = user.num_losses
    abandoned = user.num_abandoned_games
    return render_template("index.html", user_id=user_id, wins=wins, losses=losses, abandoned=abandoned)

# Solo mode
@app.route("/solo", methods=["GET"])
def get_solo():
    cur_game = session["current_solo_game"]
    return render_template("solo.html", game=cur_game)

@app.route("/restart", methods=["POST"])
def restart():
    game = dict_to_game(session["current_solo_game"])
    if game.get_state() == "In Progress":
        user_id = session["user_id"]
        user = User.query.get_or_404(user_id)
        user.num_abandoned_games += 1
        db.session.commit()

    game.restart(6, 7)
    session["current_solo_game"] = game.to_dict()
    return session["current_solo_game"]

@app.route("/move/<direction>", methods=["POST"])
def make_move(direction):
    game = dict_to_game(session["current_solo_game"])
    if game.get_state() == "In Progress":
        game.move(direction)
        session["current_solo_game"] = game.to_dict()

        user_id = session["user_id"]
        user = User.query.get_or_404(user_id)
        if game.get_state() == "Won":
            user.num_wins += 1
        if game.get_state() == "Lost":
            user.num_losses += 1
        db.session.commit()
        
        return session["current_solo_game"]

    abort(400)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
