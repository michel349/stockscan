from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from models import db, Produit, Historique, CommandeDA

from config import (
    DESTINATIONS, DEST_COLORS_HEX,
    MAIL_EXPEDITEUR, MAIL_MOT_DE_PASSE, MAIL_DESTINATAIRE
)
from models import db, Produit, Historique, CommandeDA
from pdf import generate_commande_pdf, generate_journalier_pdf, generate_commande_da_pdf

bp = Blueprint('main', __name__)


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

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
    rows = Historique.query.order_by(
        Historique.date.desc(), Historique.heure.desc()
    ).all()
    commandes = {}
    for r in rows:
        if r.cmd_id not in commandes:
            commandes[r.cmd_id] = {
                'id':          r.cmd_id,
                'date':        r.date,
                'heure':       r.heure,
                'destination': r.destination,
                'produits':    [],
                'nb_articles': 0,
            }
        commandes[r.cmd_id]['produits'].append({
            'code':        r.code,
            'nom':         r.nom,
            'quantite':    r.quantite,
            'stock_apres': r.stock_apres,
        })
        commandes[r.cmd_id]['nb_articles'] += r.quantite

    return sorted(
        commandes.values(),
        key=lambda c: (c['date'], c['heure']),
        reverse=True
    )


def envoyer_mail_commande(commande, action="nouvelle"):
    if not MAIL_EXPEDITEUR or not MAIL_DESTINATAIRE:
        print("⚠️  Mail non configuré, envoi ignoré")
        return

    try:
        action_label = {
            'nouvelle': 'NOUVELLE COMMANDE',
            'modifiée': 'COMMANDE MODIFIÉE',
        }.get(action, action.upper())

        sujet = f"[{action_label}] {commande['id']} — {commande['destination']}"

        corps_lignes = [
            f"Commande   : {commande['id']}",
            f"Destination: {commande['destination']}",
            f"Date       : {commande['date']} à {commande['heure']}",
            f"Action     : {action}",
            "",
            "Produits :",
        ]
        for p in commande['produits']:
            corps_lignes.append(
                f"  - {p.get('nom', '')} ({p.get('code', '')}) x{p.get('quantite', 0)}"
            )
        corps = "\n".join(corps_lignes)

        pdf_buffer = generate_commande_da_pdf(commande)

        msg = MIMEMultipart()
        msg['From']    = MAIL_EXPEDITEUR
        msg['To']      = MAIL_DESTINATAIRE
        msg['Subject'] = sujet
        msg.attach(MIMEText(corps, 'plain', 'utf-8'))

        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_buffer.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="commande_{commande["id"]}.pdf"'
        )
        msg.attach(part)

        try:
            # ✅ Version qui marche sur Railway avec STARTTLS
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(MAIL_EXPEDITEUR, MAIL_MOT_DE_PASSE)
                smtp.send_message(msg)
        except Exception as mail_err:
            print(f"⚠️ Echec envoi mail (continué normalement): {mail_err}")

        print(f"✅ Mail envoyé pour {commande['id']} ({action})")

    except Exception as e:
        print(f"❌ Erreur envoi mail : {e}")


# ══════════════════════════════════════════════════════════════
#  PAGES
# ══════════════════════════════════════════════════════════════

@bp.route('/')
def index():
    return render_template(
        'index.html',
        destinations=DESTINATIONS,
        dest_colors=DEST_COLORS_HEX
    )


@bp.route('/commandes_da')
def commandes_da_page():
    return render_template(
        'commandes_da.html',
        destinations=DESTINATIONS,
        dest_colors=DEST_COLORS_HEX
    )


# ══════════════════════════════════════════════════════════════
#  API STOCK / SCAN / COMMANDES CLASSIQUES
# ══════════════════════════════════════════════════════════════

@bp.route('/api/stock')
def api_stock():
    produits = Produit.query.order_by(Produit.categorie, Produit.nom).all()
    return jsonify([
        {
            'code':      p.code,
            'nom':       p.nom,
            'categorie': p.categorie,
            'stock':     p.stock,
        }
        for p in produits
    ])


@bp.route('/api/scan', methods=['POST'])
def api_scan():
    data = request.json
    code = normalise_code(data.get('code', ''))

    produit = Produit.query.filter_by(code=code).first()
    if not produit:
        return jsonify({'found': False})

    return jsonify({
        'found':     True,
        'code':      produit.code,
        'nom':       produit.nom,
        'categorie': produit.categorie,
        'stock':     produit.stock,
    })


@bp.route('/api/valider', methods=['POST'])
def api_valider():
    data        = request.json
    destination = data.get('destination')
    produits    = data.get('produits', [])

    if not destination or destination not in DESTINATIONS:
        return jsonify({'ok': False, 'error': 'Destination invalide'})
    if not produits:
        return jsonify({'ok': False, 'error': 'Aucun produit'})

    now    = datetime.now()
    cmd_id = nouvelle_commande_id()
    alertes = []

    for p in produits:
        code = normalise_code(p.get('code', ''))
        qte  = p.get('quantite', 0)
        if qte <= 0:
            continue

        produit = Produit.query.filter_by(code=code).first()
        if not produit:
            continue

        produit.stock = max(0, produit.stock - qte)
        if produit.stock <= 0:
            alertes.append(f"{produit.nom} ({code})")

        db.session.add(Historique(
            cmd_id      = cmd_id,
            date        = now.strftime('%Y-%m-%d'),
            heure       = now.strftime('%H:%M:%S'),
            destination = destination,
            code        = code,
            nom         = produit.nom,
            quantite    = qte,
            stock_apres = produit.stock,
        ))

    db.session.commit()

    return jsonify({
        'ok':      True,
        'cmd_id':  cmd_id,
        'alertes': alertes,
    })


@bp.route('/api/historique')
def api_historique():
    return jsonify(load_historique())


@bp.route('/api/journalier')
def api_journalier():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    rows = Historique.query.filter_by(date=date)\
                           .order_by(Historique.heure.desc()).all()

    commandes = {}
    for r in rows:
        if r.cmd_id not in commandes:
            commandes[r.cmd_id] = {
                'id':          r.cmd_id,
                'date':        r.date,
                'heure':       r.heure,
                'destination': r.destination,
                'produits':    [],
                'nb_articles': 0,
            }
        commandes[r.cmd_id]['produits'].append({
            'code':        r.code,
            'nom':         r.nom,
            'quantite':    r.quantite,
            'stock_apres': r.stock_apres,
        })
        commandes[r.cmd_id]['nb_articles'] += r.quantite

    return jsonify({
        'date':      date,
        'commandes': sorted(
            commandes.values(),
            key=lambda c: (c['date'], c['heure']),
            reverse=True
        ),
    })


# ══════════════════════════════════════════════════════════════
#  PDF
# ══════════════════════════════════════════════════════════════

@bp.route('/api/pdf/commande/<cmd_id>')
def api_pdf_commande(cmd_id):
    rows = Historique.query.filter_by(cmd_id=cmd_id).all()
    if not rows:
        return 'Commande introuvable', 404

    commande = {
        'id':          cmd_id,
        'date':        rows[0].date,
        'heure':       rows[0].heure,
        'destination': rows[0].destination,
        'produits': [
            {
                'code':        r.code,
                'nom':         r.nom,
                'quantite':    r.quantite,
                'stock_apres': r.stock_apres,
            }
            for r in rows
        ],
    }

    buf = generate_commande_pdf(commande)
    return send_file(buf, mimetype='application/pdf',
                     download_name=f'{cmd_id}.pdf')


@bp.route('/api/pdf/journalier')
def api_pdf_journalier():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    rows = Historique.query.filter_by(date=date)\
                           .order_by(Historique.destination, Historique.heure).all()

    commandes = {}
    for r in rows:
        if r.cmd_id not in commandes:
            commandes[r.cmd_id] = {
                'id':          r.cmd_id,
                'date':        r.date,
                'heure':       r.heure,
                'destination': r.destination,
                'produits':    [],
            }
        commandes[r.cmd_id]['produits'].append({
            'code':        r.code,
            'nom':         r.nom,
            'quantite':    r.quantite,
            'stock_apres': r.stock_apres,
        })

    buf = generate_journalier_pdf(date, list(commandes.values()))
    return send_file(buf, mimetype='application/pdf',
                     download_name=f'journalier_{date}.pdf')


# ══════════════════════════════════════════════════════════════
#  API COMMANDES DA
# ══════════════════════════════════════════════════════════════

@bp.route('/api/commandes_da/nouvelle', methods=['POST'])
def api_nouvelle_commande_da():
    try:
        data     = request.json
        dest     = data.get('destination')
        produits = data.get('produits', [])

        if not dest or dest not in DESTINATIONS:
            return jsonify({'ok': False, 'error': 'Destination invalide'})
        if not produits:
            return jsonify({'ok': False, 'error': 'Aucun produit'})

        now    = datetime.now()
        cmd_id = 'DA-' + now.strftime('%Y%m%d-%H%M%S')

date_retrait = data.get('date_retrait')
if date_retrait:
    try:
        date_retrait = datetime.strptime(date_retrait, '%Y-%m-%d').date()
    except:
        date_retrait = None
else:
    date_retrait = None

        for p in produits:
            if p.get('quantite', 0) > 0:
                db.session.add(CommandeDA(
                    cmd_id      = cmd_id,
                    date        = now.strftime('%Y-%m-%d'),
                    heure       = now.strftime('%H:%M:%S'),
                    destination = dest,
                    statut      = 'en_attente',
                    code        = p['code'],
                    nom         = p['nom'],
                    quantite    = p['quantite'],
                    date_retrait = date_retrait
                ))

        db.session.commit()

        commande_mail = {
            'id':          cmd_id,
            'date':        now.strftime('%Y-%m-%d'),
            'heure':       now.strftime('%H:%M'),
            'destination': dest,
            'produits':    [p for p in produits if p.get('quantite', 0) > 0],
        }

        # ✅ On répond d'abord IMMEDIATEMENT à l'utilisateur
        response = jsonify({'ok': True, 'cmd_id': cmd_id})

        # ✅ Puis on envoie le mail EN ARRIERE PLAN sans attendre
        import threading
        threading.Thread(
            target=envoyer_mail_commande,
            args=(commande_mail, 'nouvelle'),
            daemon=True
        ).start()

        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500


@bp.route('/api/commandes_da/modifier', methods=['POST'])
def api_modifier_commande_da():
    data     = request.json
    cmd_id   = data.get('cmd_id')
    produits = data.get('produits', [])

    if not cmd_id:
                return jsonify({'ok': False, 'error': 'ID commande manquant'})

    existing = CommandeDA.query.filter_by(cmd_id=cmd_id).first()
    if not existing:
        return jsonify({'ok': False, 'error': 'Commande introuvable'})
    dest = existing.destination

    CommandeDA.query.filter_by(cmd_id=cmd_id).delete()

    now = datetime.now()
    for p in produits:
        if p.get('quantite', 0) > 0:
            db.session.add(CommandeDA(
                cmd_id      = cmd_id,
                date        = now.strftime('%Y-%m-%d'),
                heure       = now.strftime('%H:%M:%S'),
                destination = dest,
                statut      = 'en_attente',
                code        = p['code'],
                nom         = p['nom'],
                quantite    = p['quantite'],
            ))

    db.session.commit()

    commande_mail = {
        'id':          cmd_id,
        'date':        now.strftime('%Y-%m-%d'),
        'heure':       now.strftime('%H:%M'),
        'destination': dest,
        'produits':    [p for p in produits if p.get('quantite', 0) > 0],
    }

    # ✅ On répond d'abord IMMEDIATEMENT à l'utilisateur
    response = jsonify({'ok': True})

    # ✅ Puis on envoie le mail EN ARRIERE PLAN sans attendre
    import threading
    threading.Thread(
        target=envoyer_mail_commande,
        args=(commande_mail, 'modifiée'),
        daemon=True
    ).start()

    return response


@bp.route('/api/commandes_da/supprimer', methods=['POST'])
def api_supprimer_commande_da():
    data   = request.json
    cmd_id = data.get('cmd_id')

    if not cmd_id:
        return jsonify({'ok': False, 'error': 'ID commande manquant'})

    deleted = CommandeDA.query.filter_by(cmd_id=cmd_id).delete()
    db.session.commit()

    if deleted == 0:
        return jsonify({'ok': False, 'error': 'Commande introuvable'})
    return jsonify({'ok': True})


@bp.route('/api/commandes_da')
def api_commandes_da():
    rows = CommandeDA.query.order_by(
        CommandeDA.date.desc(), CommandeDA.heure.desc()
    ).all()
    commandes = {}
    for r in rows:
        if r.cmd_id not in commandes:
            commandes[r.cmd_id] = {
                'id':          r.cmd_id,
                'date':        r.date,
                'heure':       r.heure,
                'destination': r.destination,
                'statut':      r.statut,
                'produits':    [],
            }
        commandes[r.cmd_id]['produits'].append({
            'code':     r.code,
            'nom':      r.nom,
            'quantite': r.quantite,
        })
    return jsonify({'ok': True, 'commandes': list(commandes.values())})


@bp.route('/api/commandes_da/pdf/<cmd_id>')
def api_pdf_commande_da(cmd_id):
    rows = CommandeDA.query.filter_by(cmd_id=cmd_id).all()
    if not rows:
        return 'Commande introuvable', 404

    commande = {
        'id':          cmd_id,
        'date':        rows[0].date,
        'heure':       rows[0].heure,
        'destination': rows[0].destination,
        'produits': [
            {'code': r.code, 'nom': r.nom, 'quantite': r.quantite}
            for r in rows
        ],
    }

    buf = generate_commande_da_pdf(commande)
    return send_file(buf, mimetype='application/pdf',
                     download_name=f'{cmd_id}.pdf')


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


@bp.route('/stock_info')
def stock_info():
    total    = Produit.query.count()
    ruptures = Produit.query.filter(Produit.stock <= 0).count()
    return jsonify({
        'ok':             True,
        'total_produits': total,
        'ruptures':       ruptures
    })


# ══════════════════════════════════════════════════════════════
#  ANCIENNES ROUTES (compatibilité)
# ══════════════════════════════════════════════════════════════

@bp.route('/scanner', methods=['POST'])
def scanner():
    data        = request.json
    destination = data.get('destination')
    code        = normalise_code(data.get('code', ''))

    if not destination or destination not in DESTINATIONS:
        return jsonify({'ok': False, 'error': 'Destination invalide'})

    produit = Produit.query.get(code)
    if not produit:
        return jsonify({'ok': False, 'error': f'Code {code} introuvable'})

    return jsonify({
        'ok':      True,
        'code':    code,
        'nom':     produit.nom,
        'stock':   produit.stock,
        'warning': produit.stock <= 0
    })


@bp.route('/valider_commande', methods=['POST'])
def valider_commande():
    data        = request.json
    destination = data.get('destination')
    produits    = data.get('produits', [])

    if not destination or destination not in DESTINATIONS:
        return jsonify({'ok': False, 'error': 'Destination invalide'})
    if not produits:
        return jsonify({'ok': False, 'error': 'Aucun produit'})

    now    = datetime.now()
    cmd_id = nouvelle_commande_id()

    for p in produits:
        code    = normalise_code(p.get('code', ''))
        qte     = int(p.get('quantite', 0))
        produit = Produit.query.get(code)
        if not produit:
            continue
        produit.stock -= qte
        stock_apres    = produit.stock

        db.session.add(Historique(
            cmd_id      = cmd_id,
            date        = now.strftime('%Y-%m-%d'),
            heure       = now.strftime('%H:%M:%S'),
            destination = destination,
            code        = code,
            nom         = produit.nom,
            quantite    = qte,
            stock_apres = stock_apres,
        ))

    db.session.commit()
    return jsonify({'ok': True, 'cmd_id': cmd_id})


@bp.route('/export_pdf/<cmd_id>')
def export_pdf(cmd_id):
    commandes = load_historique()
    commande  = next((c for c in commandes if c['id'] == cmd_id), None)
    if not commande:
        return "Commande introuvable", 404
    buffer   = generate_commande_pdf(commande)
    filename = f"bon_{cmd_id}.pdf"
    return send_file(buffer, as_attachment=True,
                     download_name=filename, mimetype='application/pdf')


@bp.route('/export_journalier')
def export_journalier():
    date_str       = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    toutes         = load_historique()
    commandes_jour = [c for c in toutes if c['date'] == date_str]
    if not commandes_jour:
        return "Aucune commande ce jour", 404
    buffer   = generate_journalier_pdf(date_str, commandes_jour)
    filename = f"journalier_{date_str}.pdf"
    return send_file(buffer, as_attachment=True,
                     download_name=filename, mimetype='application/pdf')

@bp.route('/commandes_da_liste')
def commandes_da_liste():
    lignes = CommandeDA.query.filter_by(statut='en_attente').all()

    # Grouper par cmd_id
    grouped = {}
    for li in lignes:
        if li.cmd_id not in grouped:
            grouped[li.cmd_id] = {
                'id':          li.cmd_id,
                'destination': li.destination,
                'date':        li.date,
                'heure':       li.heure,
                'date_retrait': li.date_retrait,
                'produits':    []
            }
        p = Produit.query.get(li.code)
        grouped[li.cmd_id]['produits'].append({
            'code':     li.code,
            'nom':      li.nom,
            'quantite': li.quantite,
            'stock':    p.stock if p else 0
        })

    result = sorted(grouped.values(), key=lambda x: x['date'] + x['heure'], reverse=True)
    return jsonify({'commandes': result})


@bp.route('/valider_commande_da', methods=['POST'])
def valider_commande_da():
    cmd_id = request.json.get('cmd_id')
    lignes = CommandeDA.query.filter_by(cmd_id=cmd_id).all()
    if not lignes:
        return jsonify({'ok': False, 'error': 'Commande introuvable'})

    for li in lignes:
        li.statut = 'validee'
    db.session.commit()
    return jsonify({'ok': True})

# ══════════════════════════════════════════════════════════════
#  ROUTE DYNAMIQUE EN DERNIER ⚠️
# ══════════════════════════════════════════════════════════════

@bp.route('/api/commandes_da/<destination>')
def api_commandes_da_par_dest(destination):
    rows = CommandeDA.query.filter_by(destination=destination)\
                           .order_by(CommandeDA.date.desc(), CommandeDA.heure.desc()).all()

    commandes = {}
    for r in rows:
        if r.cmd_id not in commandes:
            commandes[r.cmd_id] = {
                'id':          r.cmd_id,
                'date':        r.date,
                'heure':       r.heure,
                'destination': r.destination,
                'statut':      r.statut,
                'produits':    [],
            }
        commandes[r.cmd_id]['produits'].append({
            'code':     r.code,
            'nom':      r.nom,
            'quantite': r.quantite,
        })

    return jsonify({'ok': True, 'commandes': list(commandes.values())})

