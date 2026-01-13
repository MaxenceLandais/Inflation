import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
import os

PANIER = [
    {
        "nom": "Lait demi-écrémé Carrefour Classic 1L",
        "url": "https://www.carrefour.fr/p/lait-demi-ecreme-demi-ecreme-carrefour-classic-3276554163158",
        # On essaie plusieurs sélecteurs possibles pour le prix
        "selectors": [".pdp-price-container__price", ".ds-product-card__price", ".product-price"] 
    }
]

async def get_price(browser, url, selectors):
    page = await browser.new_page()
    # On agrandit la fenêtre pour simuler un vrai écran
    await page.set_viewport_size({"width": 1280, "height": 800})
    
    try:
        print(f"Navigation vers {url}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        # On attend un peu pour laisser passer les scripts anti-bot
        await asyncio.sleep(5)

        price_text = None
        for selector in selectors:
            try:
                # On attend que l'un des sélecteurs apparaisse
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    price_text = await element.inner_text()
                    break
            except:
                continue
        
        if not price_text:
            # SI CA ECHOUE : On prend une photo pour comprendre pourquoi !
            await page.screenshot(path="error_debug.png")
            print("Prix non trouvé. Capture d'écran 'error_debug.png' enregistrée.")
            return None
        
        price_clean = price_text.replace(',', '.')
        price_match = re.search(r"(\d+\.\d+|\d+)", price_clean)
        return float(price_match.group(1)) if price_match else None
        
    except Exception as e:
        print(f"Erreur : {e}")
        await page.screenshot(path="error_critical.png")
        return None
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        results = {"date": datetime.now().isoformat(), "produits": []}

        for produit in PANIER:
            prix = await get_price(browser, produit['url'], produit['selectors'])
            if prix:
                print(f"Succès : {prix} €")
                results["produits"].append({"nom": produit['nom'], "prix": prix})

        await browser.close()

        if results["produits"]:
            with open('prices_history.json', 'a', encoding='utf-8') as f:
                f.write(json.dumps(results, ensure_ascii=False) + "\n")
        else:
            # On crée un fichier vide ou on touche le fichier pour éviter l'erreur Git
            if not os.path.exists('prices_history.json'):
                open('prices_history.json', 'a').close()

if __name__ == "__main__":
    asyncio.run(main())
