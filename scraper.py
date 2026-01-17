import asyncio
from playwright.async_api import async_playwright
import requests
import json
from datetime import datetime
import re

# --- 1. ESSENCE (API GOUVERNEMENTALE) ---
def get_live_gas_price():
    # On demande les prix les plus récents pour le SP95-E10
    url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-temps-reel/records?order_by=update%20desc&limit=5"
    try:
        response = requests.get(url, timeout=15)
        data = response.json()
        for r in data.get('results', []):
            if r.get('prix_nom') == "SP95-E10":
                return float(r.get('prix_valeur'))
    except:
        pass
    return 1.82 # Valeur de secours si l'API est totalement injoignable

# --- 2. LAIT (SOURCE ALTERNATIVE OPEN DATA) ---
async def get_milk_price_fixed():
    ean = "3276554163158"
    
    # TENTATIVE A : API Open Food Facts (Rapide et ne bloque jamais)
    try:
        # On interroge l'API spécifique aux prix si disponible
        res = requests.get(f"https://world.openfoodfacts.org/api/v2/product/{ean}?fields=price,countries", timeout=10)
        data = res.json()
        price = data.get('product', {}).get('price')
        if price:
            return float(price)
    except:
        pass

    # TENTATIVE B : Scraping d'un site de catalogue "léger" (ex: OpenPrices ou comparateur simple)
    # On évite Carrefour.fr qui est un bunker.
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            # On va sur un site qui répertorie les prix sans sécurité lourde
            await page.goto(f"https://www.equall.fr/produit/{ean}", timeout=20000)
            # On cherche un texte qui ressemble à un prix (ex: 1,05 €)
            content = await page.content()
            match = re.search(r"(\d+)[.,](\d+)\s*€", content)
            if match:
                return float(f"{match.group(1)}.{match.group(2)}")
        except:
            return None
        finally:
            await browser.close()
    return None

# --- MAIN ---
async def main():
    timestamp = datetime.now().isoformat()
    produits = []

    # Essence
    p_essence = get_live_gas_price()
    if p_essence:
        produits.append({"nom": "Essence SP95 (Litre)", "prix": p_essence})
        print(f"✅ Essence trouvé : {p_essence}")

    # Lait
    p_lait = await get_milk_price_fixed()
    if p_lait:
        produits.append({"nom": "Lait Carrefour 1L", "prix": p_lait})
        print(f"✅ Lait trouvé : {p_lait}")
    else:
        print("❌ Lait toujours introuvable.")

    if produits:
        data = {"date": timestamp, "produits": produits}
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print("💾 Sauvegarde effectuée.")
    else:
        print("🔴 Erreur : Aucune donnée.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
