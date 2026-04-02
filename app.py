from flask import Flask
from config import DATABASE_URL
from models import db
from routes import bp
from models import db, Produit, Historique

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(bp)

# Crée les tables si elles existent pas
with app.app_context():
    db.create_all()



def init_db_if_empty():
    """Lance l'init seulement si la table produits est vide"""
    try:
        if Produit.query.count() == 0:
            # colle ici le contenu de la fonction init() du init_db.py
            # (la partie qui insère les produits et l'historique)
            pass
    except:
        pass

with app.app_context():
    db.create_all()
    init_db_if_empty()

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("  📦 STOCK SCAN v2 — PostgreSQL/SQLite")
    print("=" * 50)
    print("  🌐 Interface : http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
