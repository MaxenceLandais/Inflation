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
        await page.goto(site['url'], wait_until="networkidle", timeout=60000)
        
        # Technique 1 : Chercher dans les balises Meta (Auchan adore ça)
        if not prix:
            meta_price = await page.get_attribute("meta[property='product:price:amount']", "content")
            if meta_price:
                prix = float(meta_price.replace(',', '.'))

        # Technique 2 : Chercher dans le JSON-LD (Intermarché/Leclerc)
        if not prix:
            scripts = await page.locator('script[type="application/ld+json"]').all()
            for script in scripts:
                content = await script.inner_text()
                if '"price":' in content:
                    match = re.search(r'"price":\s*"([\d.]+)"', content)
                    if match:
                        prix = float(match.group(1))
                        break

        # Technique 3 : La méthode RegEx (ton sauveur pour Carrefour)
        if not prix:
            await page.wait_for_timeout(3000)
            elements = await page.get_by_text(re.compile(r"\d+[,.]\d+\s?€")).all()
            for el in elements:
                text = await el.inner_text()
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    val = float(f"{match.group(1)}.{match.group(2)}")
                    if val > 0.5: # Éviter les promos ou centimes
                        prix = val
                        break

        if prix:
            print(f"✅ {site['nom']} : {prix} €")
    except Exception as e:
        print(f"⚠️ Erreur technique {site['nom']}")
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
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"date": timestamp, "releves": resultats}, ensure_ascii=False) + "\n")
        print(f"💾 Sauvegarde effectuée ({len(resultats)} prix).")

if __name__ == "__main__":
    asyncio.run(main())
