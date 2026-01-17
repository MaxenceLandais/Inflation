import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import requests
import json
from datetime import datetime
import re

# --- FONCTION ESSENCE (API FIABLE) ---
def get_live_gas_price():
    url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-temps-reel/records?limit=100"
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        prices = [r['prix_valeur'] for r in data.get('results', []) if r.get('prix_nom') == "SP95-E10" and r.get('prix_valeur')]
        if prices:
            return round(sum(prices) / len(prices), 3)
    except:
        pass
    return None

# --- FONCTION LAIT (SCRAPING FURTIF) ---
async def get_carrefour_price():
    url = "https://www.carrefour.fr/p/lait-demi-ecreme-demi-ecreme-carrefour-classic-3276554163158"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # On active le mode Stealth pour contourner les protections
        await stealth_async(page)
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            # On attend que le prix apparaisse (on utilise un sélecteur générique de prix Carrefour)
            element = await page.wait_for_selector(".pdp-price-container", timeout=15000)
            if element:
                text = await element.inner_text()
                # Nettoyage : "1,05 €" -> 1.05
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    return float(f"{match.group(1)}.{match.group(2)}")
        except Exception as e:
            print(f"Erreur Carrefour: {e}")
        finally:
            await browser.close()
    return None

# --- MAIN ---
async def main():
    timestamp = datetime.now().isoformat()
    produits = []

    # 1. Récupération Essence
    prix_essence = get_live_gas_price()
    if prix_essence:
        produits.append({"nom": "Essence SP95 (Litre)", "prix": prix_essence})

    # 2. Récupération Lait
    prix_lait = await get_carrefour_price()
    if prix_lait:
        produits.append({"nom": "Lait Carrefour 1L", "prix": prix_lait})

    if produits:
        data = {"date": timestamp, "produits": produits}
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"Mise à jour réussie : {len(produits)} produits.")
    else:
        print("Aucun prix n'a pu être récupéré.")

if __name__ == "__main__":
    asyncio.run(main())
