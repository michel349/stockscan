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
#  PDF COMMANDE DA
# ════════════════════════════════════════════════
def generate_commande_da_pdf(commande):
    """
    Même format que generate_commande_pdf mais titre 'DEMANDE D'APPROVISIONNEMENT'
    commande = {
        'id':          'DA-...',
        'destination': 'DA1',
        'date':        '2025-01-15',
        'heure':       '14:32',
        'produits':    [{'code', 'nom', 'quantite'}, ...]
    }
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=2*cm
    )

    GRIS         = colors.HexColor('#f2f2f2')
    GRIS2        = colors.HexColor('#bbbbbb')
    couleur_dest = get_dest_color(commande.get('destination', ''))
    story        = []

    produits    = commande.get('produits', [])
    nb_articles = sum(p.get('quantite', 0) for p in produits)
    commentaire = commande.get('commentaire', '')

    # ── En-tête : titre à gauche, destination + date à droite ──
    entete = Table(
        [[
            "DEMANDE D'APPROVISIONNEMENT",
            commande.get('destination', '')
        ], [
            "",
            f"{commande.get('date', '')}  {commande.get('heure', '')}"
        ]],
        colWidths=[11*cm, 6*cm]
    )
    entete.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (0, 0),   'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (0, 0),   16),
        ('FONTNAME',      (1, 0), (1, 0),   'Helvetica-Bold'),
        ('FONTSIZE',      (1, 0), (1, 0),   16),
        ('FONTSIZE',      (1, 1), (1, 1),   11),
        ('ALIGN',         (1, 0), (1, -1),  'RIGHT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW',     (0, -1), (-1, -1), 2, couleur_dest),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 8),
    ]))
    story.append(entete)
    story.append(Spacer(1, 0.4*cm))

    # ── Commentaire en haut (lu avant la préparation) ──
    if commentaire:
        commentaire = (commentaire.replace('&', '&')
                                  .replace('<', '<')
                                  .replace('>', '>'))
        style_commentaire = ParagraphStyle(
            'commentaire', fontSize=10, leading=13, fontName='Helvetica'
        )
        story.append(Paragraph(
            f"<b>Commentaire :</b> {commentaire}", style_commentaire
        ))
        story.append(Spacer(1, 0.3*cm))

    # ── Produits : un seul tableau, catégories en lignes grises ──
    groupes = defaultdict(list)
    for p in produits:
        cat = (p.get('categorie') or 'DIVERS').upper()
        groupes[cat].append(p)

    rows   = [['Produit', 'Qté', 'OK']]
    styles = [
        ('FONTNAME',      (0, 0), (-1,  0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1,  0), 9),
        ('LINEBELOW',     (0, 0), (-1,  0), 1, colors.black),
        ('FONTNAME',      (0, 1), (0,  -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (0,  -1), 11),
        ('FONTNAME',      (1, 1), (1,  -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (1, 1), (1,  -1), 13),
        ('ALIGN',         (1, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]

    for cat_name in sorted(groupes.keys()):
        i = len(rows)
        rows.append([cat_name, '', ''])
        styles += [
            ('SPAN',       (0, i), (-1, i)),
            ('BACKGROUND', (0, i), (-1, i), GRIS),
            ('FONTNAME',   (0, i), (-1, i), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, i), (-1, i), 9),
            ('ALIGN',      (0, i), (-1, i), 'LEFT'),
        ]
        for p in sorted(groupes[cat_name], key=lambda x: x.get('nom', '')):
            j = len(rows)
            rows.append([p.get('nom', ''), str(p.get('quantite', 0)), ''])
            styles += [
                ('LINEBELOW', (0, j), (-1, j), 0.3, GRIS2),
                ('BOX',       (2, j), (2,  j), 0.8, colors.black),  # case à cocher
            ]

    prod_table = Table(rows, colWidths=[13.5*cm, 2.5*cm, 1*cm], repeatRows=1)
    prod_table.setStyle(TableStyle(styles))
    story.append(prod_table)

    # ── Total ──
    story.append(Spacer(1, 0.5*cm))
    style_total = ParagraphStyle(
        'total', fontSize=12, alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    story.append(Paragraph(
        f"TOTAL : {nb_articles} articles / {len(produits)} références",
        style_total
    ))

    # ── Numéro de page ──
    def pied_de_page(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(A4[0] - 2*cm, 1.2*cm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=pied_de_page, onLaterPages=pied_de_page)
    buffer.seek(0)
    return buffer


# ════════════════════════════════════════════════
#  PDF JOURNALIER
# ════════════════════════════════════════════════
def generate_journalier_pdf(date_str, commandes):
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

    style_titre = ParagraphStyle(
        'titre', fontSize=18, alignment=TA_CENTER,
        backColor=VERT, textColor=colors.white,
        spaceAfter=4, spaceBefore=4,
        borderPadding=(10, 10, 10, 10)
    )
    story.append(Paragraph(
        "<font color='white'><b>RÉCAPITULATIF JOURNALIER</b></font>",
        style_titre
    ))
    story.append(Spacer(1, 0.4*cm))

    produits_cumul = defaultdict(lambda: {'nom': '', 'quantite': 0, 'destinations': set()})
    for cmd in commandes:
        for p in cmd.get('produits', []):
            code = p.get('code', '')
            produits_cumul[code]['nom']       = p.get('nom', '')
            produits_cumul[code]['quantite'] += p.get('quantite', 0)
            produits_cumul[code]['destinations'].add(cmd.get('destination', ''))

    nb_commandes = len(commandes)
    nb_produits  = len(produits_cumul)
    total_unites = sum(p['quantite'] for p in produits_cumul.values())
    toutes_dests = sorted(set(d for p in produits_cumul.values() for d in p['destinations']))

    try:
        from datetime import datetime
        date_affiche = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        date_affiche = date_str

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
