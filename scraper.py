import asyncio
from playwright.async_api import async_playwright
import requests
import json
from datetime import datetime
import re

# --- FONCTION ESSENCE (API GOUVERNEMENTALE - 100% FIABLE) ---
def get_live_gas_price():
    url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-temps-reel/records?limit=100"
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        # On ne garde que le SP95-E10, le standard actuel
        prices = [r['prix_valeur'] for r in data.get('results', []) if r.get('prix_nom') == "SP95-E10" and r.get('prix_valeur')]
        if prices:
            # On arrondit à 3 décimales pour la précision
            return round(sum(prices) / len(prices), 3)
    except Exception as e:
        print(f"Erreur API Essence: {e}")
    return None

# --- FONCTION LAIT (SCRAPING CARREFOUR "FAIT MAISON") ---
async def get_carrefour_price():
    url = "https://www.carrefour.fr/p/lait-demi-ecreme-demi-ecreme-carrefour-classic-3276554163158"
    async with async_playwright() as p:
        # Lancement du navigateur avec l'argument magique pour cacher le mode automation
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"] 
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # LE SECRET DU STEALTH SANS LIBRAIRIE :
        # On injecte un script qui supprime la variable "webdriver" du navigateur
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()
        
        try:
            print(f"Scraping Carrefour en cours...")
            # On va sur la page
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # On cherche le prix
            element = await page.wait_for_selector(".pdp-price-container, .ds-product-card__price", timeout=15000)
            if element:
                text = await element.inner_text()
                # Regex pour extraire "1,05" ou "1.05"
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    return float(f"{match.group(1)}.{match.group(2)}")
        except Exception as e:
            print(f"Erreur Scraping Carrefour : {e}")
        finally:
            await browser.close()
    return None

# --- EXÉCUTION ---
async def main():
    timestamp = datetime.now().isoformat()
    produits_presents = []

    # 1. Essence
    prix_essence = get_live_gas_price()
    if prix_essence:
        produits_presents.append({"nom": "Essence SP95 (Litre)", "prix": prix_essence})
        print(f"✅ Essence : {prix_essence} €")

    # 2. Lait
    prix_lait = await get_carrefour_price()
    if prix_lait:
        produits_presents.append({"nom": "Lait Carrefour 1L", "prix": prix_lait})
        print(f"✅ Lait : {prix_lait} €")

    if produits_presents:
        data = {"date": timestamp, "produits": produits_presents}
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print("Sauvegarde terminée.")
    else:
        print("Aucune donnée récupérée.")

if __name__ == "__main__":
    asyncio.run(main())
