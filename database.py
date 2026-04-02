from models import db, Produit, Historique, CommandeDA
from datetime import datetime


def normalise_code(code):
    c = str(code).strip()
    if 'E+' in c or 'e+' in c:
        try:
            c = str(int(float(c)))
        except:
            pass
    return c


# ═══ CATALOGUE ═══

def load_catalogue():
    produits = Produit.query.all()
    return {p.code: p.to_dict() for p in produits}


def update_stock(code, new_stock):
    p = Produit.query.get(code)
    if p:
        p.stock = new_stock
        db.session.commit()
        return True
    return False


# ═══ HISTORIQUE ═══

def append_historique(cmd_id, dest, code, nom, qty, stock_apres):
    now = datetime.now()
    h = Historique(
        cmd_id=cmd_id,
        date=now.strftime('%Y-%m-%d'),
        heure=now.strftime('%H:%M:%S'),
        destination=dest,
        code=code,
        nom=nom,
        quantite=qty,
        stock_apres=stock_apres,
    )
    db.session.add(h)
    db.session.commit()


def load_historique():
    rows = Historique.query.order_by(Historique.id.desc()).all()
    commandes = {}

    for r in rows:
        if r.cmd_id not in commandes:
            commandes[r.cmd_id] = {
                'id': r.cmd_id,
                'date': r.date,
                'heure': r.heure,
                'destination': r.destination,
                'produits': [],
                'nb_articles': 0,
            }
        commandes[r.cmd_id]['produits'].append({
            'code': r.code,
            'nom': r.nom,
            'quantite': r.quantite,
            'stock_apres': r.stock_apres,
        })
        commandes[r.cmd_id]['nb_articles'] += r.quantite

    return sorted(commandes.values(), key=lambda c: (c['date'], c['heure']), reverse=True)


# ═══ COMMANDES DA ═══

def save_commande_da(cmd_id, dest, produits):
    now = datetime.now()
    for p in produits:
        c = CommandeDA(
            cmd_id=cmd_id,
            date=now.strftime('%Y-%m-%d'),
            heure=now.strftime('%H:%M:%S'),
            destination=dest,
            statut='en_attente',
            code=p['code'],
            nom=p['nom'],
            quantite=p['quantite'],
        )
        db.session.add(c)
    db.session.commit()


def load_commandes_da():
    rows = CommandeDA.query.order_by(CommandeDA.id.desc()).all()
    commandes = {}

    for r in rows:
        if r.cmd_id not in commandes:
            commandes[r.cmd_id] = {
                'id': r.cmd_id,
                'date': r.date,
                'heure': r.heure,
                'destination': r.destination,
                'statut': r.statut,
                'produits': [],
                'nb_articles': 0,
            }
        commandes[r.cmd_id]['produits'].append({
            'code': r.code,
            'nom': r.nom,
            'quantite': r.quantite,
        })
        commandes[r.cmd_id]['nb_articles'] += r.quantite

    return sorted(commandes.values(), key=lambda c: (c['date'], c['heure']), reverse=True)


def modifier_commande_da(cmd_id, produits):
    # Récupérer la destination avant suppression
    existing = CommandeDA.query.filter_by(cmd_id=cmd_id).first()
    if not existing:
        return None
    dest = existing.destination

    # Supprimer les anciennes lignes
    CommandeDA.query.filter_by(cmd_id=cmd_id).delete()

    # Réinsérer
    now = datetime.now()
    for p in produits:
        if p.get('quantite', 0) > 0:
            c = CommandeDA(
                cmd_id=cmd_id,
                date=now.strftime('%Y-%m-%d'),
                heure=now.strftime('%H:%M:%S'),
                destination=dest,
                statut='en_attente',
                code=p['code'],
                nom=p['nom'],
                quantite=p['quantite'],
            )
            db.session.add(c)
    db.session.commit()
    return dest
