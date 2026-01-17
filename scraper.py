import asyncio
from playwright.async_api import async_playwright
import re
import json
from datetime import datetime

async def get_carrefour_lait_diagnostic():
    url = "https://www.carrefour.fr/s?q=3276554163158"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("🚀 Tentative d'accès...")
            # On augmente le temps de chargement
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # On attend un peu pour laisser les scripts de prix charger
            await page.wait_for_timeout(5000)

            # --- DIAGNOSTIC : On prend une photo de ce que voit le bot ---
            await page.screenshot(path="debug_carrefour.png")
            print("📸 Capture d'écran sauvegardée sous 'debug_carrefour.png'")

            # On essaie un sélecteur plus large (n'importe quel texte avec un symbole €)
            price_element = await page.locator("text=/\\d+[,.]\\d+\\s?€/").first
            
            if await price_element.is_visible():
                text = await price_element.inner_text()
                print(f"💰 Texte trouvé : {text}")
                match = re.search(r"(\d+)[.,](\d+)", text)
                if match:
                    return float(f"{match.group(1)}.{match.group(2)}")
            else:
                # Si le sélecteur précis échoue, on liste les classes CSS présentes pour comprendre
                print("❌ Prix non visible. Contenu de la page partiel.")
                
        except Exception as e:
            print(f"❌ Erreur fatale : {e}")
            await page.screenshot(path="error_page.png")
        finally:
            await browser.close()
    return None

async def main():
    prix = await get_carrefour_lait_diagnostic()
    if prix:
        print(f"✅ Prix validé : {prix} €")
        # ... sauvegarde JSON ...
    else:
        print("🔴 Échec critique. Regarde les captures d'écran dans les artefacts GitHub.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
