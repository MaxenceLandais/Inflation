import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re

# Ton panier avec l'URL réelle de la bouteille de lait
PANIER = [
    {
        "nom": "Lait demi-écrémé Carrefour Classic 1L",
        "url": "https://www.carrefour.fr/p/lait-demi-ecreme-demi-ecreme-carrefour-classic-3276554163158",
        # Sélecteur spécifique pour le prix principal chez Carrefour
        "selector": ".pdp-price-container__price" 
    }
]

async def get_price(browser, url, selector):
    page = await browser.new_page()
    
    # On définit un User-Agent moderne pour éviter d'être détecté comme bot
    await page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    try:
        # On va sur la page
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # On attend que le prix soit visible
        await page.wait_for_selector(selector, timeout=15000)
        
        # On récupère le texte brut (ex: "1,05 €" ou "1€05")
        price_text = await page.inner_text(selector)
        
        # Nettoyage avec Regex pour extraire le nombre
        # Remplace la virgule par un point et garde uniquement chiffres et points
        price_clean = price_text.replace(',', '.')
        price_match = re.search(r"(\d+\.\d+|\d+)", price_clean)
        
        if price_match:
            return float(price_match.group(1))
        return None
        
    except Exception as e:
        print(f"Erreur sur {url}: {e}")
        return None
    finally:
        await page.close()

async def main():
    async with async_playwright() as p:
        # Lancement du navigateur
        browser = await p.chromium.launch(headless=True)
        
        timestamp = datetime.now().isoformat()
        daily_results = {
            "date": timestamp,
            "produits": []
        }

        for produit in PANIER:
            print(f"Récupération du prix : {produit['nom']}...")
            prix = await get_price(browser, produit['url'], produit['selector'])
            
            if prix:
                print(f"Prix trouvé : {prix} €")
                daily_results["produits"].append({
                    "nom": produit['nom'],
                    "prix": prix
                })
            else:
                print(f"Échec de la récupération pour {produit['nom']}")

        await browser.close()

        # On ajoute le résultat au fichier historique
        if daily_results["produits"]:
            with open('prices_history.json', 'a', encoding='utf-8') as f:
                f.write(json.dumps(daily_results, ensure_ascii=False) + "\n")
            print("Fichier history.json mis à jour.")

if __name__ == "__main__":
    asyncio.run(main())
