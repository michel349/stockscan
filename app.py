from flask import Flask
from config import DATABASE_URL
from models import db, Produit, Historique, CommandeDA
from routes import bp

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
app.register_blueprint(bp)


def init_db_if_empty():
    if Produit.query.count() == 0:
        print("🔄 Base vide — import du catalogue...")

        produits = [
            # BOISSONS
            ("CAPRISUN", "CAPRISUN MULTIVIT POCHE 20CL *40", "BOISSONS", 3, 0, 0),
            ("50COCA", "COCA COLA 50CL *24", "BOISSONS", 11, 0, 0),
            ("33COCHE1", "COCA COLA CHERRY SLIM CAN 33CL *24", "BOISSONS", 11, 0, 0),
            ("33COCASLIM", "COCA COLA SLIM CAN 33CL *24", "BOISSONS", 14, 0, 0),
            ("50CRISTACV", "CRISTALINE CITRON PET 50CL *24", "BOISSONS", 11, 0, 0),
            ("50CRISTAP", "CRISTALINE EAU PLATE 50CL *24", "BOISSONS", 5, 0, 0),
            ("50CRISTAFR", "CRISTALINE FRUITS ROUGES PET 50CL *24", "BOISSONS", 25, 0, 0),
            ("50CRISTA", "CRISTALINE GAZEIFIE 50CL *24", "BOISSONS", 12, 0, 0),
            ("33FANORA1", "FANTA ORANGE SLIM 33CL *24", "BOISSONS", 11, 0, 0),
            ("FUZTPI", "FUZETEA PECHE INTENSE 40CL *12", "BOISSONS", 18, 0, 0),
            ("33FUZETEAUP1", "FUZETEA PECHE INTENSE SLIM 33CL *24", "BOISSONS", 13, 0, 0),
            ("33ICEPEC", "ICE TEA LIPTON PECHE 33CL SLIM *24", "BOISSONS", 14, 0, 0),
            ("33OAPOCA1", "OASIS POM CASSIS FRAMB SLIM 33CL *24", "BOISSONS", 10, 0, 0),
            ("50OASISTROPICAL", "OASIS TROPICAL 50CL *12", "BOISSONS", 0, 0, 0),
            ("33OASTROSLIM", "OASIS TROPICAL SLIM 33CL *24", "BOISSONS", 9, 0, 0),
            ("33ORAJAU", "ORANGINA JAUNE SLIM 33CL *24", "BOISSONS", 22, 0, 0),
            ("ORANGINAJ", "ORANGINA JAUNE 50CL *12", "BOISSONS", 2, 0, 0),
            ("50PEPSI", "PEPSI ZERO 50CL *12", "BOISSONS", 3, 0, 0),
            ("PEPMAXSLIM", "PEPSI MAX SLIM 33CL *24", "BOISSONS", 9, 0, 0),
            ("33PERCV", "PERRIER CITRVER EAU GAZ SLIM 33CL *24", "BOISSONS", 1, 0, 0),
            ("33PERR1", "PERRIER NATURE EAU GAZ SLIM 33CL *24", "BOISSONS", 3, 0, 0),
            ("25REDBULL", "REDBULL SLIM 25CL *24", "BOISSONS", 3, 0, 0),
            ("1LSANPEL", "SAN PELLIGRINO 1L *6", "BOISSONS", 0, 0, 0),
            ("50SANPEL", "SAN PELLIGRINO 50CL *24", "BOISSONS", 0, 0, 0),
            ("33SEVENUPSLIM", "SEVEN UP SLIM 33CL *24", "BOISSONS", 0, 0, 0),
            ("33SCHAGR1", "SCHWEPPES AGRUM SLIM 33CL *24", "BOISSONS", 14, 0, 0),
            ("33SPRIVAL", "SPRING VALLEY JUS TROPICAL SLIM 33CL *24", "BOISSONS", 9, 0, 0),
            ("33SPRINGVO1", "SPRING VALLEY ORANGE SLIM 33CL *24", "BOISSONS", 0, 0, 0),
            ("33SPRINGVP", "SPRING VALLEY POMME SLIM 33CL *24", "BOISSONS", 5, 0, 0),
            ("33SPRITE", "SPRITE SLIM 33CL *24", "BOISSONS", 3, 0, 0),
            ("50VOLVIC", "VOLVIC 50CL *24", "BOISSONS", 0, 0, 0),
            # BOISSONS CHAUDES
            ("CAN07G", "CAFE EXTRA EXPRESSO N°07 GRAINS", "BOISSONS CHAUDES", 0, 0, 0),
            ("CALYMAX", "CAFE LYOPHILISE MAXWELL SP.FILTRE 500G", "BOISSONS CHAUDES", 0, 0, 0),
            ("CALYDECA", "CAFE LYOPHILISE RISTRETTO DECA POCHE", "BOISSONS CHAUDES", 0, 0, 0),
            ("CANO3G", "CAFE SUPERIEUR EXPRESSO N°03 GRAINS", "BOISSONS CHAUDES", 0, 0, 0),
            ("CHOC", "CHOCOLAT VH1 VAN HOUTEN D.A. *10", "BOISSONS CHAUDES", 12, 0, 0),
            ("THECIT", "THE CITRON DA 1KG *10", "BOISSONS CHAUDES", 0, 0, 0),
            ("THEFRU", "THE FRUITS ROUGES DA 1KG *10", "BOISSONS CHAUDES", 0, 0, 0),
            ("THEMEN", "THE MENTHE DA 1KG *10", "BOISSONS CHAUDES", 0, 0, 0),
            ("CAFCAR", "VENDING CAFE CARAMEL DA 1KG *10", "BOISSONS CHAUDES", 0, 0, 0),
            ("CAFNOI", "VENDING CAPUCCINO NOISETTE 1KG *10", "BOISSONS CHAUDES", -1, 0, 0),
            ("CAFVAN", "VENDING CAPUCCINO VANILLE 1KG *10", "BOISSONS CHAUDES", 0, 0, 0),
            # LAIT/SUCRE
            ("LAITNS", "LAIT DA NON SUCRE 500G *10", "LAIT/SUCRE", 14, 0, 0),
            ("SUCSEM", "SUCRE SEMOULE D.A. 2KG *6", "LAIT/SUCRE", 0, 0, 0),
            # POTAGES
            ("DNLPOTTEXM", "DRINK A LIKE POTAGE TEX MEX 1KG *5", "POTAGES", 0, 0, 0),
            ("DNLPOTPOI", "DRINK N LIKE POTAGE POIREAU PDT 1KG *5", "POTAGES", 0, 0, 0),
            ("DNLPOTPROV", "DRINK N LIKE POTAGE PROVENCAL 1KG *5", "POTAGES", 0, 0, 0),
            ("DNLPOTTOM", "DRINK N LIKE POTAGE TOMATE 1KG *5", "POTAGES", 0, 0, 0),
            # ENCAS SALES
            ("COCRAF", "CRACKERS SAVEUR FROMAGE ET POIVRE 40G *50", "ENCAS SALES", 0, 0, 0),
            ("COCRAR", "CRAKERS ROMARIN PATATE *50", "ENCAS SALES", 0, 0, 0),
            ("COCRAT", "CRAKERS TOMATE ORIGAN *50", "ENCAS SALES", 0, 0, 0),
            ("COPATPOU", "PATES POULET *12", "ENCAS SALES", 0, 0, 0),
            ("COSALNA", "SALADE NAPOLITAINE THON *12", "ENCAS SALES", 0, 0, 0),
            ("COSALPI", "SALADE PIEMONTAISE THON *12", "ENCAS SALES", 0, 0, 0),
            ("COSALRIZ", "SALADE RIZ THON 220GR *7", "ENCAS SALES", 0, 0, 0),
            ("COSALVG", "SALADE VEGETARIENNE 220G *7", "ENCAS SALES", 0, 0, 0),
            ("SALPRO", "SALADE PROVENCALE AU POULET *7", "ENCAS SALES", 0, 0, 0),
            # BISCUITS/CONFISERIES
            ("COBALRAINOI", "BALISTO CEREALES RAISIN NOISETTE 37G *20", "BISCUITS/CONFISERIES", 3, 0, 0),
            ("COBALISCER", "BALISTO MIEL AMANDE 37G *20", "BISCUITS/CONFISERIES", 3, 0, 0),
            ("COBF2", "BARRE DE FRUITS POMME ORANGE CAROTTE 45GR *20", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("COBEL", "BELVITA PETIT DEJEUNER 50G *30", "BISCUITS/CONFISERIES", 3, 0, 0),
            ("COBOULAI", "BOUNTY CHOCO 57G *24", "BISCUITS/CONFISERIES", 4, 0, 0),
            ("SACHIPSFLO", "CHIPS SEL FLODOR 30G *40", "BISCUITS/CONFISERIES", 4, 0, 0),
            ("COTEDORLN", "COTE D'OR LAIT NOISETTE BARRE CHOCOLATEE *32", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("COCRUNCH", "CRUNCH 30G *30", "BISCUITS/CONFISERIES", 1, 0, 0),
            ("CURLYCA", "CURLY CACAHUETES 60G *30", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("GALAMA", "GALETTE MOELLEUSE SAVEUR AMANDE *24", "BISCUITS/CONFISERIES", 1, 0, 0),
            ("COGALC", "GALETTE RIZ CHOCO *20", "BISCUITS/CONFISERIES", 2, 0, 0),
            ("GAULIE", "GAUFRE LIEGEOISE 90G *30", "BISCUITS/CONFISERIES", 3, 0, 0),
            ("GERCRAAM", "GERBLE BIO CRANBERRY AMANDE *18", "BISCUITS/CONFISERIES", 3, 0, 0),
            ("GERBLEBIOGC", "GERBLE BISCUIT BIO GINGEMBRE CITRON *18", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("COGEBI", "GERBLE BISCUIT LAIT CHOCOLAT 46G *18", "BISCUITS/CONFISERIES", 5, 0, 0),
            ("COGESE", "GERBLE BISCUIT SESAME 46G *18", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("CROGER", "GERBLE CROQUANT MIEL SESAME 27G *18", "BISCUITS/CONFISERIES", 1, 0, 0),
            ("GERGALCHO", "GERBLE GALETTE MAIS CHOCO LAIT *56", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("GERCHOCLAIT", "GERBLE GALETTE MAIS CHOCOLAT LAIT *28", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("GALGERN", "GERBLE GALETTE RIZ CHOCO NOIR 33G *28", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("HARDELIR", "HARIBO SACHET 120G *30", "BISCUITS/CONFISERIES", 2, 0, 0),
            ("BARSPEKC", "KELLOGS SPECIAL K CHOCOLAT 21.5G *30", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("BARSPEK", "KELLOGS SPECIAL K FRUIT ROUGE 21.5G *30", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("COKINBUEW", "KINDER BUENO WHITE *30", "BISCUITS/CONFISERIES", 6, 0, 0),
            ("COKINBUE", "KINDER BUENO 43G *30", "BISCUITS/CONFISERIES", 3, 0, 0),
            ("COKITKATC", "KIT KAT CHUNKY 40G *24", "BISCUITS/CONFISERIES", 4, 0, 0),
            ("COLON", "KIT KAT FINGER 41.5G *36", "BISCUITS/CONFISERIES", 5, 0, 0),
            ("COLIONC", "LION 42G *24", "BISCUITS/CONFISERIES", 4, 0, 0),
            ("COLIONC15", "LION BARRE CHOCO +15% *24", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("COMM50", "M&M'S CHOCO PEANUT 45G *36", "BISCUITS/CONFISERIES", 1, 0, 0),
            ("MADNAT", "MADELEINE NATURE 84G *24", "BISCUITS/CONFISERIES", 2, 0, 0),
            ("COMAL", "MALTESERS 37G *25", "BISCUITS/CONFISERIES", 2, 0, 0),
            ("COMARS", "MARS CHOCO 51G *40", "BISCUITS/CONFISERIES", 2, 0, 0),
            ("COMAGA", "MAXI GALETTE 100G *24", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("MIKADOLAIT", "MIKADO POCKET LAIT *24", "BISCUITS/CONFISERIES", 1, 0, 0),
            ("MINISAVANE", "MINI SAVANE CHOCOLAT X2 60G *36", "BISCUITS/CONFISERIES", 1, 0, 0),
            ("GOMUNATC", "MUFFIN NATURE & PEPITES CHOCOLAT *40", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("NAPO60GX2", "NAPOLITAIN CLASSIC X2 60G *24", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("NATVALCHO", "NATURE VALLEY&DARK NUT CHO 30G *18", "BISCUITS/CONFISERIES", 0, 0, 0),
            ("CONUTS", "NUTS NOISETTE CHOCO 42G *24", "BISCUITS/CONFISERIES", 2, 0, 0),
            ("COOREO", "OREO 66G *20", "BISCUITS/CONFISERIES", 1, 0, 0),
            ("PETITECO", "PETIT ECOLIER CHOCO LAIT *23", "BISCUITS/CONFISERIES", 5, 0, 0),
            ("POMPOTEPOM", "POMPOTE ANA GRENADE SSA *48", "BISCUITS/CONFISERIES", 2, 0, 0),
            ("COPRINCE", "PRINCE CHOCOLAT 80G *20", "BISCUITS/CONFISERIES", 2, 0, 0),
            ("COSNIC", "SNICKERS 50G *40", "BISCUITS/CONFISERIES", 1, 0, 0),
            ("COTWIX", "TWIX 50G *32", "BISCUITS/CONFISERIES", 2, 0, 0),
            # GOURMALLIANCE
            ("COCECH", "BARRE DE CEREALES AU CHOCOLAT *20", "GOURMALLIANCE", 0, 0, 0),
            ("COCENO", "BARRE DE CEREALES AUX NOISETTES ENKA *20", "GOURMALLIANCE", 0, 0, 0),
            ("COCECF", "BARRE DE CEREALES CRANB ET FRAM *20", "GOURMALLIANCE", 0, 0, 0),
            ("COGOUP", "GOURDE MIXE DE POMMES BIO 90GR *55", "GOURMALLIANCE", 0, 0, 0),
            ("COCOOKM62", "GRAND COOKIE MOELLEUX BEURRE CACAH MILLET & CHIA *26", "GOURMALLIANCE", 0, 0, 0),
            ("COCOAM", "GRAND COOKIE MOELLEUX BROWNIE CHOCO *26", "GOURMALLIANCE", 0, 0, 0),
            ("COCOOK", "GRAND COOKIE MOELLEUX COCO AMANDES *26", "GOURMALLIANCE", 0, 0, 0),
            ("COGAULIE", "GRANDE GAUFFRE LIEGOISE SUCREE MI CHOCO *24", "GOURMALLIANCE", 0, 0, 0),
            ("MIXTON", "MIX TONUS BIO 35G *12", "GOURMALLIANCE", 0, 0, 0),
            ("GOUPP", "GOURDE MIXE *10", "GOURMALLIANCE", 0, 0, 0),
            ("PICKUP", "PICKUP *24", "GOURMALLIANCE", 0, 0, 0),
            ("MINCOOK", "MINI COOKIE 80G *75", "GOURMALLIANCE", 0, 0, 0),
            ("PITAPIZ", "MINI PITA 30G *50", "GOURMALLIANCE", 0, 0, 0),
            # DIVERS
            ("GOB151924", "GOBELET PLASTIQUE DA BLANC 15CL 30R *100", "DIVERS", 10, 0, 0),
            ("CHLORE", "PASTILLE JAVEL-500G-150 COMPRIMES", "DIVERS", 6, 0, 0),
            ("WH20006021", "PRODUIT LESSIVIEL POLYVALENT F300 5L", "DIVERS", 0, 0, 0),
            ("SACPOU50L", "SAC POUBELLE 50L", "DIVERS", 23, 0, 0),
            ("SPATUL", "SPATULES BOIS 105MM 60R *50", "DIVERS", 22, 0, 0),
            ("HYESSTOU", "PAPIER ESSUIE MAIN", "DIVERS", 9, 0, 0),
        ]

        for code, nom, cat, stock, mini, maxi in produits:
            p = Produit(code=code, nom=nom, categorie=cat,
                        stock=stock, stock_mini=mini, stock_maxi=maxi)
            db.session.add(p)

        print(f"✅ {len(produits)} produits importés")

        historique_data = [
            ("CMD-20260224-105500", "2026-02-24", "10:55:00", "DA1", "50COCA", "COCA COLA 50CL *24", 2, 0),
            ("CMD-20260224-105500", "2026-02-24", "10:55:00", "DA1", "SUCSEM", "SUCRE SEMOULE D.A. 2KG *6", 1, 0),
            ("CMD-20260224-112312", "2026-02-24", "11:23:12", "DA1", "50COCA", "COCA COLA 50CL *24", 1, 0),
            ("CMD-20260224-112945", "2026-02-24", "11:29:45", "DA1", "50COCA", "COCA COLA 50CL *24", 1, 0),
            ("CMD-20260224-112945", "2026-02-24", "11:29:45", "DA1", "MIKADOLAIT", "MIKADO POCKET LAIT *24", 1, 0),
            ("CMD-20260224-123055", "2026-02-24", "12:30:55", "DA2", "50COCA", "COCA COLA 50CL *24", 1, -1),
            ("CMD-20260224-123407", "2026-02-24", "12:34:07", "DA1", "50COCA", "COCA COLA 50CL *24", 1, -2),
            ("CMD-20260224-124522", "2026-02-24", "12:45:22", "DA1", "CAPRISUN", "CAPRISUN MULTIVIT POCHE 20CL *40", 5, -5),
            ("CMD-20260224-124522", "2026-02-24", "12:45:22", "DA1", "33COCHE1", "COCA COLA CHERRY SLIM CAN 33CL *24", 2, -2),
            ("CMD-20260224-124522", "2026-02-24", "12:45:22", "DA1", "50CRISTACV", "CRISTALINE CITRON PET 50CL *24", 3, -3),
            ("CMD-20260224-125848", "2026-02-24", "12:58:48", "DA2", "33COCHE1", "COCA COLA CHERRY SLIM CAN 33CL *24", 1, -3),
            ("CMD-20260224-125848", "2026-02-24", "12:58:48", "DA2", "33COCASLIM", "COCA COLA SLIM CAN 33CL *24", 1, -1),
            ("CMD-20260224-125848", "2026-02-24", "12:58:48", "DA2", "33FANORA1", "FANTA ORANGE SLIM 33CL *24", 1, -1),
            ("CMD-20260224-125848", "2026-02-24", "12:58:48", "DA2", "50CRISTACV", "CRISTALINE CITRON PET 50CL *24", 6, -9),
            ("CMD-20260306-084409", "2026-03-06", "08:44:09", "DA1", "33FUZETEAUP1", "FUZETEA PECHE INTENSE SLIM 33CL *24", 3, 13),
            ("CMD-20260306-084409", "2026-03-06", "08:44:09", "DA1", "PEPMAXSLIM", "PEPSI MAX SLIM 33CL *24", 2, 9),
            ("CMD-20260306-084409", "2026-03-06", "08:44:09", "DA1", "CAFNOI", "VENDING CAPUCCINO NOISETTE 1KG *10", 1, -1),
            ("CMD-20260306-084409", "2026-03-06", "08:44:09", "DA1", "50CRISTAFR", "CRISTALINE FRUITS ROUGES PET 50CL *24", 3, 25),
        ]

        for cmd_id, date, heure, dest, code, nom, qty, stock_apres in historique_data:
            h = Historique(
                cmd_id=cmd_id, date=date, heure=heure,
                destination=dest, code=code, nom=nom,
                quantite=qty, stock_apres=stock_apres
            )
            db.session.add(h)

        db.session.commit()
        print(f"✅ {len(historique_data)} lignes d'historique importées")
        print("🎉 Base de données prête !")
    else:
        print(f"✅ Base déjà initialisée ({Produit.query.count()} produits)")


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
