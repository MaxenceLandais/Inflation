import asyncio
from playwright.async_api import async_playwright
import playwright_stealth
import requests
import json
from datetime import datetime
import re

# --- FONCTION ESSENCE (API GOUVERNEMENTALE - FIABLE) ---
def get_live_gas_price():
    # API officielle des prix des carburants en temps réel
    url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-temps-reel/records?limit=100"
    try:
        response = requests.get(url, timeout=20)
        data = response.json()
        # On filtre sur le SP95-E10 car c'est un excellent indicateur d'inflation énergétique
        prices = [r['prix_valeur'] for r in data.get('results', []) if r.get('prix_nom') == "SP95-E10" and r.get('prix_valeur')]
        if prices:
            return round(sum(prices) / len(prices), 3)
    except Exception as e:
        print(f"Erreur API Essence: {e}")
    return None

# --- FONCTION LAIT (SCRAPING CARREFOUR) ---
async def get_carrefour_price():
    url = "https://www.carrefour.fr/p/lait-demi-ecreme-demi-ecreme-carrefour-classic-3276554163158"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # On applique le mode furtif pour éviter les blocages
        await playwright_stealth.stealth_async(page)
        
        try:
            print(f"Tentative de scraping Carrefour...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Attente d'un des sélecteurs de prix possibles
            element = await page.wait_for_selector(".pdp-price-container, .ds-product-card__price", timeout=20000)
            if element:
                text = await element.inner_text()
                # On extrait le prix avec une regex (ex: "1,05 €" -> 1.05)
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    return float(f"{match.group(1)}.{match.group(2)}")
        except Exception as e:
            print(f"Le scraping Carrefour a échoué (protection anti-bot probable) : {e}")
        finally:
            await browser.close()
    return None

# --- EXÉCUTION PRINCIPALE ---
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

    # Enregistrement si on a au moins une donnée
    if produits_presents:
        data = {"date": timestamp, "produits": produits_presents}
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print("Mise à jour du fichier prices_history.json effectuée.")
    else:
        print("Aucune donnée récupérée aujourd'hui.")

if __name__ == "__main__":
    asyncio.run(main())
