import os

# ═══ BASE DE DONNÉES ═══
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///stock.db')

if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# ═══ DESTINATIONS ═══
DESTINATIONS = ['DA1', 'DA2']

DEST_COLORS_HEX = {
    'DA1': '#2980b9',
    'DA2': '#8e44ad',
}

# ═══ CODES SPECIAUX ═══
CODE_FIN          = 'FIN'
CODE_ANNULER      = 'ANNULER'
CODE_DEST_PREFIX  = 'DEST:'

# ═══ EMAIL ═══
MAIL_EXPEDITEUR     = os.environ.get('MAIL_EXPEDITEUR', '')
MAIL_MOT_DE_PASSE   = os.environ.get('MAIL_MOT_DE_PASSE', '')
MAIL_DESTINATAIRE   = os.environ.get('MAIL_DESTINATAIRE', '')

# Serveur SMTP (par défaut Gmail, mais modifiable pour SendGrid, Mailjet, etc.)
MAIL_SERVEUR        = os.environ.get('MAIL_SERVEUR', 'smtp.gmail.com')
MAIL_PORT           = int(os.environ.get('MAIL_PORT', '587'))
MAIL_USE_TLS        = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
MAIL_USE_SSL        = os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true'
