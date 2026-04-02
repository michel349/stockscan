from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime

from config import DESTINATIONS, DEST_COLORS_HEX
from models import db, Produit, Historique, CommandeDA
from pdf import generate_commande_pdf, generate_journalier_pdf

bp = Blueprint('main', __name__)


def normalise_code(code):
    c = str(code).strip()
    if 'E+' in c or 'e+' in c:
        try:
            c = str(int(float(c)))
        except:
            pass
    return c


def nouvelle_commande_id():
    return datetime.now().strftime('CMD-%Y%m%d-%H%M%S')


def load_historique():
    """Regroupe les lignes historique par commande."""
    rows = Historique.query.order_by(Historique.date.desc(), Historique.heure.desc()).all()
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


# ── Page principale ───────────────────────────────────────────
@bp.route('/')
def index():
    return render_template(
        'index.html',
        destinations=DESTINATIONS,
        dest_colors=DEST_COLORS_HEX
    )


# ── Scanner ───────────────────────────────────────────────────
@bp.route('/scanner', methods=['POST'])
def scanner():
    data = request.json
    destination = data.get('destination')
    code = normalise_code(data.get('code', ''))

    if not destination or destination not in DESTINATIONS:
        return jsonify({'ok': False, 'error': 'Destination invalide'})

    produit = Produit.query.get(code)
    if not produit:
        return jsonify({'ok': False, 'error': f'Code {code} introuvable'})

    return jsonify({
        'ok': True,
        'code': code,
        'nom': produit.nom,
        'stock': produit.stock,
        'warning': produit.stock <= 0
    })


# ── Valider commande ──────────────────────────────────────────
@bp.route('/valider_commande', methods=['POST'])
def valider_commande():
    data = request.json
    destination = data.get('destination')
    panier = data.get('panier', {})

    if not destination or not panier:
        return jsonify({'ok': False, 'error': 'Données manquantes'})
    if destination not in DESTINATIONS:
        return jsonify({'ok': False, 'error': 'Destination invalide'})

    cmd_id = nouvelle_commande_id()
    now = datetime.now()

    for code, p in panier.items():
        code = normalise_code(code)
        nom = p['nom']
        quantite = p['quantite']

        produit = Produit.query.get(code)
        if produit:
            produit.stock -= quantite
            stock_apres = produit.stock
        else:
            stock_apres = 0

        db.session.add(Historique(
            cmd_id=cmd_id,
            date=now.strftime('%Y-%m-%d'),
            heure=now.strftime('%H:%M:%S'),
            destination=destination,
            code=code,
            nom=nom,
            quantite=quantite,
            stock_apres=stock_apres,
        ))

    db.session.commit()
    return jsonify({'ok': True, 'cmd_id': cmd_id})


# ── Stock info ────────────────────────────────────────────────
@bp.route('/stock_info')
def stock_info():
    produits = Produit.query.all()
    historique = load_historique()

    stock = [p.to_dict() for p in produits]
    return jsonify({'stock': stock, 'historique': historique})


# ── Arrivage stock ────────────────────────────────────────────
@bp.route('/arrivage', methods=['POST'])
def arrivage():
    data = request.json
    code = normalise_code(data.get('code', ''))
    qty = int(data.get('quantite', 0))

    if qty <= 0:
        return jsonify({'ok': False, 'error': 'Quantité invalide'})

    produit = Produit.query.get(code)
    if not produit:
        return jsonify({'ok': False, 'error': 'Produit introuvable'})

    produit.stock += qty
    db.session.commit()

    return jsonify({
        'ok': True,
        'nouveau_stock': produit.stock,
        'nom': produit.nom
    })


# ── Modifier stock manuellement ───────────────────────────────
@bp.route('/modifier_stock', methods=['POST'])
def modifier_stock():
    data = request.json
    code = normalise_code(data.get('code', ''))
    new_stock = int(data.get('stock', 0))

    produit = Produit.query.get(code)
    if not produit:
        return jsonify({'ok': False, 'error': 'Produit introuvable'})

    produit.stock = new_stock
    db.session.commit()
    return jsonify({'ok': True, 'nouveau_stock': new_stock})


# ── Scan code-barres action ───────────────────────────────────
@bp.route('/scan_action', methods=['POST'])
def scan_action():
    data = request.json
    code = data.get('code', '').strip()

    if code.startswith('DEST:'):
        dest = code.replace('DEST:', '')
        if dest in DESTINATIONS:
            return jsonify({'ok': True, 'action': 'set_destination', 'destination': dest})
        return jsonify({'ok': False, 'error': 'Destination inconnue'})

    if code == 'ACTION:VALIDER':
        return jsonify({'ok': True, 'action': 'valider'})
    if code == 'ACTION:VIDER':
        return jsonify({'ok': True, 'action': 'vider'})
    if code == 'ACTION:RESET_DEST':
        return jsonify({'ok': True, 'action': 'reset_destination'})

    return jsonify({'ok': True, 'action': 'produit', 'code': code})


# ── Export PDF commande ───────────────────────────────────────
@bp.route('/export_pdf/<cmd_id>')
def export_pdf(cmd_id):
    commandes = load_historique()
    commande = next((c for c in commandes if c['id'] == cmd_id), None)
    if not commande:
        return "Commande introuvable", 404
    buffer = generate_commande_pdf(commande)
    return send_file(buffer, as_attachment=True,
                     download_name=f"bon_{cmd_id}.pdf", mimetype='application/pdf')


# ── Export PDF journalier ─────────────────────────────────────
@bp.route('/export_pdf_jour/<date_str>')
def export_pdf_jour(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return "Format de date invalide (YYYY-MM-DD)", 400

    toutes = load_historique()
    commandes_jour = [c for c in toutes if c['date'] == date_str]

    if not commandes_jour:
        return "Aucune commande pour cette date", 404

    buffer = generate_journalier_pdf(date_str, commandes_jour)
    return send_file(buffer, as_attachment=True,
                     download_name=f"journalier_{date_str}.pdf", mimetype='application/pdf')


# ══════════════════════════════════════════════════════════════
#  COMMANDES DA
# ══════════════════════════════════════════════════════════════

@bp.route('/commandes_da')
def commandes_da():
    return render_template(
        'commandes_da.html',
        destinations=DESTINATIONS,
        dest_colors=DEST_COLORS_HEX
    )


@bp.route('/api/catalogue')
def api_catalogue():
    produits = Produit.query.order_by(Produit.categorie, Produit.nom).all()
    return jsonify({
        'ok': True,
        'produits': [
            {'code': p.code, 'nom': p.nom, 'categorie': p.categorie, 'stock': p.stock}
            for p in produits
        ]
    })


@bp.route('/api/commandes_da/<destination>')
def api_commandes_da(destination):
    rows = CommandeDA.query.filter_by(destination=destination).order_by(
        CommandeDA.date.desc(), CommandeDA.heure.desc()
    ).all()

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
            }
        commandes[r.cmd_id]['produits'].append({
            'code': r.code,
            'nom': r.nom,
            'quantite': r.quantite,
        })

    result = sorted(commandes.values(), key=lambda c: (c['date'], c['heure']), reverse=True)
    return jsonify({'ok': True, 'commandes': result})


@bp.route('/api/commandes_da/nouvelle', methods=['POST'])
def api_nouvelle_commande_da():
    data = request.json
    dest = data.get('destination')
    produits = data.get('produits', [])

    if not dest or not produits:
        return jsonify({'ok': False, 'error': 'Données manquantes'})

    cmd_id = 'CDA-' + datetime.now().strftime('%Y%m%d-%H%M%S')
    now = datetime.now()

    for p in produits:
        if p.get('quantite', 0) > 0:
            db.session.add(CommandeDA(
                cmd_id=cmd_id,
                date=now.strftime('%Y-%m-%d'),
                heure=now.strftime('%H:%M:%S'),
                destination=dest,
                statut='en_attente',
                code=p['code'],
                nom=p['nom'],
                quantite=p['quantite'],
            ))

    db.session.commit()
    return jsonify({'ok': True, 'cmd_id': cmd_id})


@bp.route('/api/commandes_da/modifier', methods=['POST'])
def api_modifier_commande_da():
    data = request.json
    cmd_id = data.get('cmd_id')
    produits = data.get('produits', [])

    if not cmd_id:
        return jsonify({'ok': False, 'error': 'ID commande manquant'})

    # Récupérer la destination avant de supprimer
    existing = CommandeDA.query.filter_by(cmd_id=cmd_id).first()
    if not existing:
        return jsonify({'ok': False, 'error': 'Commande introuvable'})
    dest = existing.destination

    # Supprimer les anciennes lignes
    CommandeDA.query.filter_by(cmd_id=cmd_id).delete()

    # Réinsérer les nouvelles
    now = datetime.now()
    for p in produits:
        if p.get('quantite', 0) > 0:
            db.session.add(CommandeDA(
                cmd_id=cmd_id,
                date=now.strftime('%Y-%m-%d'),
                heure=now.strftime('%H:%M:%S'),
                destination=dest,
                statut='en_attente',
                code=p['code'],
                nom=p['nom'],
                quantite=p['quantite'],
            ))

    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/commandes_da/supprimer', methods=['POST'])
def api_supprimer_commande_da():
    data = request.json
    cmd_id = data.get('cmd_id')

    if not cmd_id:
        return jsonify({'ok': False, 'error': 'ID commande manquant'})

    deleted = CommandeDA.query.filter_by(cmd_id=cmd_id).delete()
    db.session.commit()

    if deleted == 0:
        return jsonify({'ok': False, 'error': 'Commande introuvable'})
    return jsonify({'ok': True})
