import os

# ═══ BASE DE DONNÉES ═══
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///stock.db')

# Fix Render (postgres:// → postgresql://)
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# ═══ DESTINATIONS ═══
DESTINATIONS = ['DA1', 'DA2']

DEST_COLORS_HEX = {
    'DA1': '#2980b9',
    'DA2': '#8e44ad',
}

# ═══ CODES SPECIAUX ═══
CODE_FIN = 'FIN'
CODE_ANNULER = 'ANNULER'
CODE_DEST_PREFIX = 'DEST:'
