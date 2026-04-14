from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Produit(db.Model):
    __tablename__ = 'produits'

    code = db.Column(db.String(50), primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    categorie = db.Column(db.String(100), default='')
    stock = db.Column(db.Integer, default=0)
    stock_mini = db.Column(db.Integer, default=0)
    stock_maxi = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'code': self.code,
            'nom': self.nom,
            'categorie': self.categorie,
            'stock': self.stock,
            'stock_mini': self.stock_mini,
            'stock_maxi': self.stock_maxi,
        }


class Historique(db.Model):
    __tablename__ = 'historique'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cmd_id = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    heure = db.Column(db.String(8), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    nom = db.Column(db.String(200), default='')
    quantite = db.Column(db.Integer, default=0)
    stock_apres = db.Column(db.Integer, default=0)


class CommandeDA(db.Model):
    __tablename__ = 'commandes_da'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cmd_id = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    heure = db.Column(db.String(8), nullable=False)
    destination = db.Column(db.String(50), nullable=False)
    statut = db.Column(db.String(20), default='en_attente')
    code = db.Column(db.String(50), nullable=False)
    nom = db.Column(db.String(200), default='')
    quantite = db.Column(db.Integer, default=0)
    date_retrait = db.Column(db.String(10), nullable=True)


