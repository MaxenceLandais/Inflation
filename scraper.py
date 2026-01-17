import asyncio
from playwright.async_api import async_playwright
import requests
import json
from datetime import datetime
import re

# --- 1. ESSENCE (API GOUVERNEMENTALE STRICTE) ---
def get_live_gas_price():
    # On demande 100 résultats et on filtre en Python pour éviter les erreurs de syntaxe URL API
    url = "https://data.economie.gouv.fr/api/explore/v2.1/catalog/datasets/prix-des-carburants-en-france-flux-temps-reel/records?limit=100"
    try:
        response = requests.get(url, timeout=30)
        data = response.json()
        
        # On cherche le SP95-E10, et on s'assure que le prix existe (> 0.5€ pour éviter les erreurs)
        prices = []
        for r in data.get('results', []):
            if r.get('prix_nom') == "SP95-E10":
                val = r.get('prix_valeur')
                if val and isinstance(val, (int, float)) and val > 1.0:
                    prices.append(val)
        
        if prices:
            # On retourne la moyenne réelle
            return round(sum(prices) / len(prices), 3)
            
    except Exception as e:
        print(f"❌ Erreur critique API Essence: {e}")
    return None

# --- 2. LAIT (SCRAPING VIA RECHERCHE - TECHNIQUE BYPASS) ---
async def get_carrefour_price_strict():
    # ASTUCE : On cherche par code barre (EAN) dans le moteur de recherche interne
    # C'est beaucoup moins protégé que la page produit directe
    ean = "3276554163158"
    url = f"https://www.carrefour.fr/s?q={ean}"
    
    async with async_playwright() as p:
        # Lancement avec arguments pour masquer le bot
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Script pour cacher le webdriver
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        print(f"🕵️  Recherche du produit {ean} sur Carrefour...")
        
        try:
            # On va sur la page de RECHERCHE (plus rapide)
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Gestion des cookies (parfois ils bloquent la vue)
            try:
                # On essaie de cliquer sur "Continuer sans accepter" ou "Accepter" si ça apparaît
                onetrust_btn = await page.wait_for_selector("#onetrust-reject-all-handler", timeout=3000)
                if onetrust_btn:
                    await onetrust_btn.click()
                    print("🍪 Cookies fermés.")
            except:
                pass # Pas grave si pas de bannière

            # Sélecteur générique pour le prix dans une carte de résultat de recherche
            # Carrefour utilise souvent ces classes pour les grilles de produits
            selector = ".product-card-price .product-price__amount-value, .ds-product-card__price"
            
            element = await page.wait_for_selector(selector, timeout=15000)
            if element:
                text = await element.inner_text()
                # Nettoyage strict : on ne garde que les chiffres et la virgule/point
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    price = float(f"{match.group(1)}.{match.group(2)}")
                    return price
            else:
                print("❌ Sélecteur de prix non trouvé sur la page de recherche.")
                
        except Exception as e:
            print(f"❌ Erreur Scraping Strict : {e}")
        finally:
            await browser.close()
    return None

# --- MAIN ---
async def main():
    timestamp = datetime.now().isoformat()
    produits_presents = []

    # 1. ESSENCE
    prix_essence = get_live_gas_price()
    if prix_essence:
        print(f"✅ Essence (SP95-E10) : {prix_essence} €")
        produits_presents.append({"nom": "Essence SP95 (Litre)", "prix": prix_essence})
    else:
        print("⛔ IMPOSSIBLE de récupérer le prix de l'essence.")

    # 2. LAIT
    prix_lait = await get_carrefour_price_strict()
    if prix_lait:
        print(f"✅ Lait (Carrefour) : {prix_lait} €")
        produits_presents.append({"nom": "Lait Carrefour 1L", "prix": prix_lait})
    else:
        print("⛔ IMPOSSIBLE de récupérer le prix du lait.")

    # ECRITURE SEULEMENT SI TOUT EST OK (ou au moins un des deux)
    if produits_presents:
        data = {"date": timestamp, "produits": produits_presents}
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print("💾 Données réelles enregistrées.")
    else:
        # On génère une erreur explicite pour que GitHub Actions marque le run en rouge 🔴
        print("🔴 ÉCHEC TOTAL : Aucune donnée réelle récupérée.")
        exit(1) 

if __name__ == "__main__":
    asyncio.run(main())
