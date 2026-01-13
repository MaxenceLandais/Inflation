import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

async def get_price(url, selector):
    async with async_playwright() as p:
        # On lance un navigateur "headless" (invisible)
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # On simule un utilisateur réel pour éviter le blocage
        await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 ..."})
        
        try:
            await page.goto(url, wait_until="networkidle")
            # On récupère le texte du sélecteur de prix
            price_text = await page.inner_text(selector)
            # Nettoyage pour ne garder que les chiffres (ex: "1,45 €" -> 1.45)
            price = float(price_text.replace('€', '').replace(',', '.').strip())
            return price
        except Exception as e:
            print(f"Erreur lors du scraping : {e}")
            return None
        finally:
            await browser.close()

async def main():
    # Exemple : Un produit de base sur un site de drive
    # Note : Tu devras adapter l'URL et le sélecteur CSS selon le site choisi
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "produits": [
            {
                "nom": "Pâtes Penne 500g",
                "url": "URL_DU_PRODUIT_ICI",
                "selector": ".product-price", # À adapter selon le site
                "prix": await get_price("URL_DU_PRODUIT_ICI", ".product-price")
            }
        ]
    }
    
    # On sauvegarde dans un fichier JSON pour ton historique
    with open('prices_history.json', 'a') as f:
        json.dump(data, f)
        f.write('\n')
    print("Données mises à jour !")

if __name__ == "__main__":
    asyncio.run(main())
