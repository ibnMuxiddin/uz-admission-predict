import asyncio
import json
import sys
import os
import pandas as pd
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

COMBINATIONS_FILE = "data/raw/combinations.json"
OUTPUT_CSV = "data/raw/otm_2026.csv"
PROGRESS_FILE = "data/raw/progress.json"

async def get_options(page, select_id):
    return await page.evaluate(f'''() => {{
        const select = document.getElementById("{select_id}");
        if (!select) return [];
        return Array.from(select.options)
            .filter(o => o.value && o.value !== "0")
            .map(o => ({{ value: o.value, text: o.text.trim() }}));
    }}''')

async def select_and_wait(page, select_id, value, wait_for_select_id):
    if wait_for_select_id:
        await page.evaluate(f'''() => {{
            const nextSelect = document.getElementById("{wait_for_select_id}");
            if (nextSelect) {{
                nextSelect.innerHTML = '<option value="0">Kuting...</option>';
            }}
        }}''')
        
    await page.evaluate(f'''(val) => {{
        const select = document.getElementById("{select_id}");
        select.value = val;
        if (typeof $ !== "undefined") {{
            $(select).trigger("change");
        }}
        select.dispatchEvent(new Event("change", {{ bubbles: true }}));
    }}''', value)
    
    if wait_for_select_id:
        try:
            await page.wait_for_function(f"document.querySelectorAll('#{wait_for_select_id} option').length > 1", timeout=10000)
            await page.wait_for_timeout(200)
            return True
        except:
            return False
    return True

async def gather_combinations(page):
    print("Kombinatsiyalarni yig'ish boshlandi...")
    await page.goto("https://mandat.uzbmb.uz/Mandat2025", timeout=60000)
    await page.wait_for_function("document.querySelectorAll('#Regions option').length > 1", timeout=15000)
    
    combinations = []
    regions = await get_options(page, "Regions")
    
    for r in regions:
        print(f"Hudud: {r['text']}")
        ok1 = await select_and_wait(page, "Regions", r['value'], "Universities")
        if not ok1: continue
        
        universities = await get_options(page, "Universities")
        for u in universities:
            ok2 = await select_and_wait(page, "Universities", u['value'], "Faculties")
            if not ok2: continue
            
            faculties = await get_options(page, "Faculties")
            for f in faculties:
                ok3 = await select_and_wait(page, "Faculties", f['value'], "EdLanguages")
                if not ok3: continue
                
                langs = await get_options(page, "EdLanguages")
                for l in langs:
                    ok4 = await select_and_wait(page, "EdLanguages", l['value'], "EdTypes")
                    if not ok4: continue
                    
                    types = await get_options(page, "EdTypes")
                    for t in types:
                        combo = {
                            "region": r,
                            "univer": u,
                            "faculty": f,
                            "lang": l,
                            "type": t
                        }
                        combinations.append(combo)
                        
    with open(COMBINATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(combinations, f, ensure_ascii=False, indent=2)
    print(f"Jami {len(combinations)} ta kombinatsiya yig'ildi va saqlandi.")
    return combinations

async def scrape_results(page, combo):
    print(f"\nQidirilmoqda: {combo['univer']['text']} - {combo['faculty']['text']} ({combo['lang']['text']}, {combo['type']['text']})")
    
    # URL orqali to'g'ridan-to'g'ri o'tish (juda tez va ishonchli)
    url = f"https://mandat.uzbmb.uz/Mandat2025/MainSearch?website=&lang=uz&region={combo['region']['value']}&univer={combo['univer']['value']}&faculty={combo['faculty']['value']}&edlang={combo['lang']['value']}&edtype={combo['type']['value']}"
    
    try:
        await page.goto(url, timeout=60000)
    except Exception as e:
        print(f"Sahifaga o'tishda xatolik: {e}")
        return None
        
    try:
        await page.wait_for_selector("div.m3-rank-item", timeout=15000)
    except:
        print("Natijalar topilmadi (jadval yuklanmadi yoki bo'sh).")
        # Natija bo'lmasa ham bo'sh qaytaramiz (xato qilib to'xtab qolmasligi uchun)
        return {
            "hudud": combo['region']['text'],
            "otm_nomi": combo['univer']['text'],
            "yunalish_nomi": combo['faculty']['text'],
            "talim_tili": combo['lang']['text'],
            "talim_shakli": combo['type']['text'],
            "grant_kvota_soni": 0,
            "shartnoma_kvota_soni": 0,
            "grant_bali": None,
            "shartnoma_bali": None
        }

    grant_count = 0
    shartnoma_count = 0
    grant_bali = None
    shartnoma_bali = None
    
    first_shartnoma_found = False
    sahifa = 1
    
    while True:
        items = await page.locator("div.m3-rank-item").all()
        
        for item in items:
            item_text = (await item.inner_text()).lower()
            item_class = (await item.get_attribute("class") or "").lower()
            
            if "m3-rank--other" in item_class or "boshqa yo'nalish" in item_text:
                continue
                
            try:
                score_text = await item.locator(".m3-rank-score b").inner_text()
                ball = float(score_text.replace(',', '.').strip())
            except:
                ball = 0.0
                
            if "grant" in item_class or "davlat granti" in item_text:
                if not first_shartnoma_found:
                    grant_count += 1
                    grant_bali = ball 
                    
            elif "contract" in item_class or "shartnoma" in item_text:
                if not first_shartnoma_found:
                    first_shartnoma_found = True
                
                shartnoma_count += 1
                shartnoma_bali = ball  
                
        next_button = page.locator("button.page-link:has-text('Keyingi')")
        if await next_button.count() > 0:
            try:
                async with page.expect_navigation(timeout=30000):
                    await next_button.first.click()
                await page.wait_for_selector("div.m3-rank-item", timeout=15000)
                sahifa += 1
            except Exception as e:
                print(f"Keyingi sahifaga o'tishda xatolik: {e}")
                break
        else:
            break
            
    result = {
        "hudud": combo['region']['text'],
        "otm_nomi": combo['univer']['text'],
        "yunalish_nomi": combo['faculty']['text'],
        "talim_tili": combo['lang']['text'],
        "talim_shakli": combo['type']['text'],
        "grant_kvota_soni": grant_count,
        "shartnoma_kvota_soni": shartnoma_count,
        "grant_bali": grant_bali,
        "shartnoma_bali": shartnoma_bali
    }
    return result

async def main():
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    
    # Progressni o'qish (qaysi indeksgacha kelinganini bilish uchun)
    processed_index = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            processed_index = json.load(f).get("last_index", 0)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Kombinatsiyalarni o'qish yoki yig'ish
        if os.path.exists(COMBINATIONS_FILE):
            with open(COMBINATIONS_FILE, 'r', encoding='utf-8') as f:
                combinations = json.load(f)
            print(f"{COMBINATIONS_FILE} faylidan {len(combinations)} ta kombinatsiya o'qildi.")
        else:
            combinations = await gather_combinations(page)
            
        # Ma'lumotlarni yig'ish va faylga qo'shib borish
        for i in range(processed_index, len(combinations)):
            combo = combinations[i]
            res = await scrape_results(page, combo)
            
            if res:
                df = pd.DataFrame([res])
                # Agar birinchi ma'lumot bo'lsa header bilan yozamiz, bo'lmasa append qilamiz
                write_mode = 'a' if os.path.exists(OUTPUT_CSV) else 'w'
                header = not os.path.exists(OUTPUT_CSV)
                
                success = False
                while not success:
                    try:
                        df.to_csv(OUTPUT_CSV, mode=write_mode, header=header, index=False, encoding='utf-8')
                        success = True
                    except Exception as e:
                        print(f"DIQQAT! CSV faylga yozishda xatolik (Fayl Excelda ochiq bo'lishi mumkin). 10 soniyadan so'ng qayta uriniladi... Xatolik: {e}")
                        await asyncio.sleep(10)
                        
            # Progressni saqlash
            with open(PROGRESS_FILE, 'w') as f:
                json.dump({"last_index": i + 1}, f)
                
            # Serverga og'irlik tushmasligi uchun kichik pauza
            await asyncio.sleep(1)
            
        print("\nBARCHA OTM LAR UCHUN MA'LUMOTLAR YIG'ILIB BO'LDI!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
