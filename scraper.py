import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

async def get_carrefour_lait_strict():
    # URL de recherche directe par EAN (plus stable que la page produit)
    url = "https://www.carrefour.fr/s?q=3276554163158"
    
    async with async_playwright() as p:
        # On lance un navigateur avec un profil "humain"
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
            viewport={'width': 375, 'height': 667} # On simule un mobile pour alléger la page
        )
        
        page = await context.new_page()
        
        try:
            # On navigue vers la page de recherche
            await page.goto(url, wait_until="networkidle", timeout=45000)
            
            # On cherche le sélecteur du prix (Carrefour utilise souvent ces classes pour le prix principal)
            # On essaie plusieurs sélecteurs car ils varient selon les tests A/B de Carrefour
            price_selectors = [
                ".product-card-price__value",
                ".ds-product-card__price",
                ".pdp-price-container",
                "span[class*='price']"
            ]
            
            price_found = None
            for selector in price_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        text = await element.inner_text()
                        # Extraction du prix : "1,05 €" -> 1.05
                        match = re.search(r"(\d+)[.,](\d+)", text)
                        if match:
                            price_found = float(f"{match.group(1)}.{match.group(2)}")
                            break
                except:
                    continue
            
            return price_found

        except Exception as e:
            print(f"Erreur lors du scraping : {e}")
            return None
        finally:
            await browser.close()

async def main():
    timestamp = datetime.now().isoformat()
    prix_lait = await get_carrefour_lait_strict()

    if prix_lait is not None:
        data = {
            "date": timestamp,
            "produits": [{"nom": "Lait Carrefour 1L", "prix": prix_lait}]
        }
        
        # On ajoute au fichier JSON existant
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"✅ Prix du lait capturé : {prix_lait} €")
    else:
        print("❌ Échec : Impossible de lire le prix réel du lait sur Carrefour.")
        # On ne sauve rien, pour garder l'historique propre

if __name__ == "__main__":
    asyncio.run(main())
