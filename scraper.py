import requests
import json
from datetime import datetime

def get_live_gas_price():
    """Récupère le prix moyen national réel. Retourne None si échec."""
    url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-temps-reel/records?limit=20"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        # On extrait uniquement les prix valides pour le SP95-E10
        prices = [r['prix_valeur'] for r in data.get('results', []) if r.get('prix_nom') == "SP95-E10" and r.get('prix_valeur')]
        
        if prices:
            return round(sum(prices) / len(prices), 3)
    except:
        pass
    return None

def get_live_food_price(ean):
    """Récupère le prix réel sur Open Food Facts. Retourne None si absent."""
    url = f"https://world.openfoodfacts.org/api/v2/product/{ean}?fields=price"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        price = data.get('product', {}).get('price')
        if price:
            return float(price)
    except:
        pass
    return None

def main():
    timestamp = datetime.now().isoformat()
    produits_presents = []

    # Test du Lait
    prix_lait = get_live_food_price("3276554163158")
    if prix_lait:
        produits_presents.append({"nom": "Lait Carrefour 1L", "prix": prix_lait})

    # Test de l'Essence
    prix_essence = get_live_gas_price()
    if prix_essence:
        produits_presents.append({"nom": "Essence SP95 (Litre)", "prix": prix_essence})

    # On n'enregistre que si on a au moins un produit avec un prix réel
    if produits_presents:
        data = {
            "date": timestamp,
            "produits": produits_presents
        }
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"Succès : {len(produits_presents)} produits mis à jour.")
    else:
        print("Erreur : Aucun prix n'a pu être récupéré en direct. Aucune donnée enregistrée.")

if __name__ == "__main__":
    main()
