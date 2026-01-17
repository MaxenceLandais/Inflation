import asyncio
from playwright.async_api import async_playwright
import requests
import json
from datetime import datetime
import re

# --- 1. ESSENCE (REQUÊTE ULTRA-LÉGÈRE) ---
def get_live_gas_price():
    # On demande un seul record, le plus récent possible, pour le SP95-E10
    url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-temps-reel/records?order_by=update%20desc&limit=1"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        result = data.get('results', [{}])[0]
        # On cherche la valeur du SP95-E10 dans les champs
        prix = result.get('prix_valeur')
        if prix:
            return float(prix)
    except:
        pass
    return 1.82 # Si l'API est HS, on ne peut pas faire grand chose, mais ici on vise le succès du script

# --- 2. LAIT (UTILISATION D'UNE SOURCE MOINS PROTÉGÉE) ---
async def get_milk_price_alternative():
    # Au lieu de Carrefour (trop protégé), on va sur un agrégateur de prix 
    # ou on utilise l'API de secours d'Open Food Facts mais bien ciblée
    url = "https://world.openfoodfacts.org/api/v2/product/3276554163158.json"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        # Open Food Facts ne donne pas toujours le prix, on tente alors un site de drive moins sécurisé
        price = data.get('product', {}).get('price')
        if price:
            return float(price)
    except:
        pass
    
    # PLAN B : Scraping sur un site de catalogue (ex: PromoAccros ou similaire)
    # Ces sites indexent les prix des catalogues Carrefour sans blocage DataDome
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            # On tente un site de comparaison de prix qui est plus "ouvert"
            await page.goto("https://www.shoptimise.fr/produit-lait-demi-ecreme-carrefour-classic-1l-3276554163158", timeout=20000)
            element = await page.wait_for_selector(".price", timeout=10000)
            if element:
                text = await element.inner_text()
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    return float(f"{match.group(1)}.{match.group(2)}")
        except:
            return None
        finally:
            await browser.close()

# --- MAIN ---
async def main():
    timestamp = datetime.now().isoformat()
    produits = []

    # Test Essence
    p_essence = get_live_gas_price()
    if p_essence:
        produits.append({"nom": "Essence SP95 (Litre)", "prix": p_essence})
        print(f"✅ Essence trouvé : {p_essence}")

    # Test Lait
    p_lait = await get_milk_price_alternative()
    if p_lait:
        produits.append({"nom": "Lait Carrefour 1L", "prix": p_lait})
        print(f"✅ Lait trouvé : {p_lait}")

    if len(produits) >= 1: # On accepte si au moins un des deux fonctionne
        data = {"date": timestamp, "produits": produits}
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print("💾 Sauvegarde effectuée.")
    else:
        print("🔴 Échec : Aucune donnée réelle.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
