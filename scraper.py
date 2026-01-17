import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def get_carrefour_milk_price():
    url = "https://www.carrefour.fr/p/lait-demi-ecreme-demi-ecreme-carrefour-classic-3276554163158"
    
    async with async_playwright() as p:
        # Lancement du navigateur avec un User-Agent crédible
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"Accès à Carrefour : {url}")
            # On attend que la page soit chargée
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # On attend que le prix soit présent dans le DOM (plusieurs sélecteurs possibles)
            # Carrefour change souvent ses classes CSS
            selectors = [".pdp-price-container", ".ds-product-card__price", ".product-price"]
            
            price_text = None
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=10000)
                    if element:
                        price_text = await element.inner_text()
                        break
                except:
                    continue
            
            if not price_text:
                return None

            # Nettoyage : "1,05 €" -> 1.05
            price_clean = price_text.replace(',', '.')
            match = re.search(r"(\d+\.\d+|\d+)", price_clean)
            
            if match:
                return float(match.group(1))
            
        except Exception as e:
            print(f"Erreur Scraping : {e}")
        finally:
            await browser.close()
    return None

async def main():
    prix_lait = await get_carrefour_milk_price()
    
    if prix_lait:
        timestamp = datetime.now().isoformat()
        data = {
            "date": timestamp,
            "produits": [{"nom": "Lait Carrefour 1L", "prix": prix_lait}]
        }
        
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"✅ Prix du lait enregistré : {prix_lait} €")
    else:
        print("❌ Impossible de récupérer le prix. Carrefour a peut-être bloqué la requête.")

if __name__ == "__main__":
    asyncio.run(main())
