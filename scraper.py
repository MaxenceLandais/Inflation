import asyncio
from playwright.async_api import async_playwright
import re
import json
from datetime import datetime

async def get_carrefour_lait_diagnostic():
    # URL de recherche par code-barres
    url = "https://www.carrefour.fr/s?q=3276554163158"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="fr-FR" # On force la locale française pour éviter les redirections US
        )
        page = await context.new_page()
        
        try:
            print("🚀 Tentative d'accès avec IP VPN...")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # On attend un peu que les prix se chargent
            await page.wait_for_timeout(5000)
            await page.screenshot(path="debug_carrefour.png")
            print("📸 Capture d'écran effectuée.")

            # --- CORRECTION DE LA SYNTAXE ICI ---
            # On cherche un texte qui contient "€"
            price_locator = page.get_by_text(re.compile(r"\d+[,.]\d+\s?€")).first
            
            # On vérifie si l'élément est là avant de demander le texte
            if await price_locator.is_visible():
                text = await price_locator.inner_text()
                print(f"💰 Texte trouvé : {text}")
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    return float(f"{match.group(1)}.{match.group(2)}")
            else:
                print("❌ Le prix n'est pas visible sur la page.")
                
        except Exception as e:
            print(f"❌ Erreur : {e}")
        finally:
            await browser.close()
    return None

async def main():
    prix = await get_carrefour_lait_diagnostic()
    if prix:
        timestamp = datetime.now().isoformat()
        # On ne garde que le lait pour l'instant
        data = {"date": timestamp, "produits": [{"nom": "Lait Carrefour 1L", "prix": prix}]}
        with open('prices_history.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"✅ Prix validé et sauvé : {prix} €")
    else:
        print("🔴 Échec : Regarde l'image 'debug_carrefour.png' dans les Artifacts.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
