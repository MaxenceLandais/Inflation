import asyncio
from playwright.async_api import async_playwright
import re
import json
from datetime import datetime

async def get_milk_price_strict():
    # On utilise l'URL de recherche, plus légère
    url = "https://www.carrefour.fr/s?q=3276554163158"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # On simule un utilisateur sur un écran classique
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("🚀 Connexion via VPN en cours...")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Attente du sélecteur de prix (Carrefour change souvent, on en teste deux)
            # .product-card-price__value est souvent utilisé dans les résultats de recherche
            element = await page.wait_for_selector(".product-card-price__value, .ds-product-card__price", timeout=20000)
            
            if element:
                text = await element.inner_text()
                print(f"Brut trouvé : {text}")
                # Nettoyage pour garder le format 0.00
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    return float(f"{match.group(1)}.{match.group(2)}")
        except Exception as e:
            print(f"❌ Erreur : {e}")
        finally:
            await browser.close()
    return None

async def main():
    prix = await get_milk_price_strict()
    if prix:
        timestamp = datetime.now().isoformat()
        data = {"date": timestamp, "produits": [{"nom": "Lait Carrefour 1L", "prix": prix}]}
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"✅ Succès : {prix} €")
    else:
        print("🔴 Échec malgré le VPN.")
        exit(1) # Force l'erreur pour voir le log GitHub

if __name__ == "__main__":
    asyncio.run(main())
