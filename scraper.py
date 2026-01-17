import asyncio
from playwright.async_api import async_playwright
import json
import re
from datetime import datetime

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
        await page.goto(site['url'], wait_until="domcontentloaded", timeout=60000)
        
        # On attend que la page soit vraiment prête
        await page.wait_for_timeout(7000) 

        # Tentative de récupération du prix (on boucle pour éviter le 0.0)
        for attempt in range(3):
            # On cherche tous les éléments qui contiennent un symbole €
            elements = await page.get_by_text(re.compile(r"\d+[,.]\d+\s?€")).all()
            
            for el in elements:
                text = await el.inner_text()
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    valeur = float(f"{match.group(1)}.{match.group(2)}")
                    if valeur > 0.10: # On ignore les prix ridicules ou à 0
                        prix = valeur
                        break
            
            if prix: break
            await page.wait_for_timeout(2000) # On attend un peu si on n'a rien trouvé

        if prix:
            print(f"✅ {site['nom']} : {prix} €")
        else:
            print(f"❌ Prix non trouvé ou invalide pour {site['nom']}")
            
    except Exception as e:
        print(f"⚠️ Erreur technique sur {site['nom']}")
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
                resultats.append({"enseigne": site['nom'], "prix": prix})
        await browser.close()

    if resultats:
        data_to_save = {"date": timestamp, "releves": resultats}
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data_to_save, ensure_ascii=False) + "\n")
        print(f"💾 Sauvegarde effectuée ({len(resultats)} prix).")
    else:
        print("🔴 Échec total.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
