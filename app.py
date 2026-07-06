from flask import Flask
from config import DATABASE_URL
from models import db, Produit, Historique, CommandeDA
from routes import bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(bp)
