import asyncio
from playwright.async_api import async_playwright
import json
import re
from datetime import datetime

# --- CONFIGURATION DES SOURCES ---
# On utilise tes liens directs + le bypass Carrefour
SITES_LAIT = [
    {"nom": "Carrefour", "url": "https://www.carrefour.fr/s?q=3276554163158"},
    {"nom": "Auchan", "url": "https://www.auchan.fr/candia-grandlait-lait-frais-demi-ecreme-de-montagne/pr-C1171071"},
    {"nom": "Leclerc", "url": "https://www.e.leclerc/fp/lait-pasteurise-demi-ecreme-en-bouteille-1-l-delisse-3564700611630"},
    {"nom": "Intermarche", "url": "https://www.intermarche.com/produit/lait-demi-ecreme-sterilise-uht-francais-issu-de-vaches-qui-paturent/3250390012030"}
]

async def scrape_milk_site(browser, site):
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="fr-FR"
    )
    page = await context.new_page()
    prix = None
    
    try:
        print(f"🔍 Scan {site['nom']}...")
        # Timeout de 60s pour compenser la lenteur potentielle du VPN
        await page.goto(site['url'], wait_until="networkidle", timeout=60000)
        
        # Pause pour laisser les prix s'afficher (anti-bot bypass)
        await page.wait_for_timeout(5000)

        # Méthode RegEx : cherche le premier texte type "1,05 €"
        price_locator = page.get_by_text(re.compile(r"\d+[,.]\d+\s?€")).first
        
        if await price_locator.is_visible():
            text = await price_locator.inner_text()
            match = re.search(r"(\d+)[.,](\d+)", text)
            if match:
                prix = float(f"{match.group(1)}.{match.group(2)}")
                print(f"✅ {site['nom']} : {prix} €")
        else:
            print(f"❌ Prix non trouvé pour {site['nom']}")
            
    except Exception as e:
        print(f"⚠️ Erreur sur {site['nom']} : {e}")
    finally:
        await context.close()
    
    return prix

async def main():
    timestamp = datetime.now().isoformat()
    resultats = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        for site in SITES_LAIT:
            prix = await scrape_milk_site(browser, site)
            if prix:
                resultats.append({
                    "enseigne": site['nom'],
                    "prix": prix
                })
        
        await browser.close()

    # SAUVEGARDE STRICTE
    if resultats:
        data_to_save = {
            "date": timestamp,
            "releves": resultats
        }
        
        # On écrit une nouvelle ligne dans le fichier historique
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data_to_save, ensure_ascii=False) + "\n")
        
        print(f"💾 Terminé. {len(resultats)} prix réels enregistrés.")
    else:
        print("🔴 ÉCHEC TOTAL : Aucun prix n'a pu être récupéré aujourd'hui.")
        exit(1) # Le job GitHub Actions passera en rouge

if __name__ == "__main__":
    asyncio.run(main())
