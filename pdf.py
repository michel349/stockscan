from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from io import BytesIO
from collections import defaultdict
from config import DEST_COLORS_HEX


def get_dest_color(destination):
    hex_color = DEST_COLORS_HEX.get(destination, '#2980b9')
    return colors.HexColor(hex_color)


# ════════════════════════════════════════════════
#  PDF PAR COMMANDE
# ════════════════════════════════════════════════
def generate_commande_pdf(commande):
    """
    commande = {
        'id':          'CMD-...',
        'destination': 'Bloc A',
        'date':        '2025-01-15',
        'heure':       '14:32',        ← optionnel
        'produits':    [{'code', 'nom', 'quantite'}, ...]
    }
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm
    )

    GRIS         = colors.HexColor('#f8f9fa')
    GRIS2        = colors.HexColor('#dee2e6')
    couleur_dest = get_dest_color(commande.get('destination', ''))
    story        = []

    # ── En-tête ──────────────────────────────────────────────
    style_titre = ParagraphStyle(
        'titre', fontSize=18, alignment=TA_CENTER,
        backColor=couleur_dest, textColor=colors.white,
        spaceAfter=4, spaceBefore=4,
        borderPadding=(10, 10, 10, 10)
    )
    story.append(Paragraph("<font color='white'><b>BON DE PRÉLÈVEMENT</b></font>", style_titre))
    story.append(Spacer(1, 0.4*cm))

    # ── Infos commande ────────────────────────────────────────
    produits  = commande.get('produits', [])
    nb_articles = sum(p.get('quantite', 0) for p in produits)

    heure = commande.get('heure', '')

    info_data = [
        ['Commande :',    commande.get('id', '')],
        ['Destination :', commande.get('destination', '')],
        ['Date :',        commande.get('date', '')],
        ['Heure :',       heure],
        ['Nb produits :', str(len(produits))],
        ['Nb articles :', str(nb_articles)],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME',      (0, 0), (0,  -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('TEXTCOLOR',     (0, 0), (0,  -1), couleur_dest),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=couleur_dest))
    story.append(Spacer(1, 0.4*cm))

    # ── Tableau produits ──────────────────────────────────────
    rows = [['✓', 'Code', 'Produit', 'Quantité']]
    for p in produits:
        rows.append(['☐', p.get('code', ''), p.get('nom', ''), str(p.get('quantite', 0))])

    prod_table = Table(rows, colWidths=[1*cm, 3.5*cm, 10*cm, 2.5*cm], repeatRows=1)
    prod_table.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1,  0), couleur_dest),
        ('TEXTCOLOR',      (0, 0), (-1,  0), colors.white),
        ('FONTNAME',       (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1,  0), 10),
        ('ALIGN',          (0, 0), (-1,  0), 'CENTER'),
        ('FONTNAME',       (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',       (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRIS]),
        ('ALIGN',          (3, 1), (3,  -1), 'CENTER'),
        ('ALIGN',          (0, 1), (0,  -1), 'CENTER'),
        ('GRID',           (0, 0), (-1, -1), 0.5, GRIS2),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 7),
        ('TOPPADDING',     (0, 0), (-1, -1), 7),
    ]))
    story.append(prod_table)
    story.append(Spacer(1, 1*cm))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ════════════════════════════════════════════════
#  PDF JOURNALIER
# ════════════════════════════════════════════════
def generate_journalier_pdf(date_str, commandes):
    """
    date_str   = '2025-01-15'
    commandes  = liste de commandes (même format que ci-dessus)
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm
    )

    VERT  = colors.HexColor('#27ae60')
    GRIS  = colors.HexColor('#f8f9fa')
    GRIS2 = colors.HexColor('#dee2e6')
    story = []

    # ── En-tête ──────────────────────────────────────────────
    style_titre = ParagraphStyle(
        'titre', fontSize=18, alignment=TA_CENTER,
        backColor=VERT, textColor=colors.white,
        spaceAfter=4, spaceBefore=4,
        borderPadding=(10, 10, 10, 10)
    )
    story.append(Paragraph("<font color='white'><b>RÉCAPITULATIF JOURNALIER</b></font>", style_titre))
    story.append(Spacer(1, 0.4*cm))

    # ── Regroupement des produits ─────────────────────────────
    produits_cumul = defaultdict(lambda: {'nom': '', 'quantite': 0, 'destinations': set()})
    for cmd in commandes:
        for p in cmd.get('produits', []):
            code = p.get('code', '')
            produits_cumul[code]['nom']        = p.get('nom', '')
            produits_cumul[code]['quantite']  += p.get('quantite', 0)
            produits_cumul[code]['destinations'].add(cmd.get('destination', ''))

    nb_commandes  = len(commandes)
    nb_produits   = len(produits_cumul)
    total_unites  = sum(p['quantite'] for p in produits_cumul.values())
    toutes_dests  = sorted(set(d for p in produits_cumul.values() for d in p['destinations']))

    # Formatage date lisible
    try:
        from datetime import datetime
        date_affiche = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        date_affiche = date_str

    # ── Infos résumé ──────────────────────────────────────────
    info_data = [
        ['Date :',                  date_affiche],
        ['Nb commandes :',          str(nb_commandes)],
        ['Destinations :',          ' · '.join(toutes_dests)],
        ['Nb produits distincts :', str(nb_produits)],
        ['Total unités sorties :',  str(total_unites)],
    ]
    info_table = Table(info_data, colWidths=[5*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
        ('FONTNAME',      (0, 0), (0,  -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('TEXTCOLOR',     (0, 0), (0,  -1), VERT),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=VERT))
    story.append(Spacer(1, 0.4*cm))

    # ── Tableau récap ─────────────────────────────────────────
    rows = [['Code', 'Produit', 'Destinations', 'Qté totale']]
    for code, p in sorted(produits_cumul.items()):
        dests = ' + '.join(sorted(p['destinations']))
        rows.append([code, p['nom'], dests, str(p['quantite'])])

    prod_table = Table(rows, colWidths=[3*cm, 9*cm, 3*cm, 2.5*cm], repeatRows=1)
    prod_table.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1,  0), VERT),
        ('TEXTCOLOR',      (0, 0), (-1,  0), colors.white),
        ('FONTNAME',       (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1,  0), 10),
        ('ALIGN',          (0, 0), (-1,  0), 'CENTER'),
        ('FONTNAME',       (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',       (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRIS]),
        ('ALIGN',          (2, 1), (3,  -1), 'CENTER'),
        ('GRID',           (0, 0), (-1, -1), 0.5, GRIS2),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 7),
        ('TOPPADDING',     (0, 0), (-1, -1), 7),
    ]))
    story.append(prod_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
