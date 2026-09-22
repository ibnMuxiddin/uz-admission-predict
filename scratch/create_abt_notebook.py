import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

nb = new_notebook()

nb.cells.extend([
    new_markdown_cell("# abt.uz saytidan ma'lumotlarni yig'ish (Test Bosqichi)\n\nSizning talabingizga binoan, ma'lumotlarni bittada yig'masdan, avvaliga Jupyter Notebook da bosqichma-bosqich test qilamiz. Hamma narsa to'g'ri ishlayotganiga ishonch hosil qilganimizdan so'ng to'liq skript yozamiz."),
    
    new_code_cell("import requests\nfrom bs4 import BeautifulSoup\nimport pandas as pd\n\nHEADERS = {'User-Agent': 'Mozilla/5.0'}"),
    
    new_markdown_cell("## 1-qadam: OTMlar ro'yxatini va URL (slug) larini ajratib olish\n\n`abt.uz/university` sahifasidan barcha OTMlarning maxsus URL manzillarini yig'amiz."),
    
    new_code_cell("url = 'https://abt.uz/university'\nr = requests.get(url, headers=HEADERS)\nsoup = BeautifulSoup(r.content, 'html.parser')\n\nuniversities = []\nfor a in soup.find_all('a', href=True):\n    href = a['href']\n    if '/university/' in href:\n        name = a.text.strip()\n        slug = href.split('/')[-1]\n        if name and slug:\n            universities.append({'nomi': name, 'slug': slug})\n            \n# Takrorlanmas qilish uchun\nuniversities = [dict(t) for t in {tuple(d.items()) for d in universities}]\n\nprint(f\"Topilgan OTMlar soni: {len(universities)}\")\nprint(\"Dastlabki 5 ta OTM:\")\nfor u in universities[:5]:\n    print(f\"{u['nomi']} -> slug: {u['slug']}\")"),
    
    new_markdown_cell("## 2-qadam: Bitta OTM misolida ma'lumotlarni tortish\n\nKeling, `buxoro-davlat-tibbiyot-instituti` ning 2023-yil, kunduzgi ta'lim, o'zbek tili yo'nalishi bo'yicha ma'lumotlarni tortib ko'ramiz.\nURL formati: `https://abt.uz/university/view?slug={slug}&year={year}&type={form}&lang={lang}`"),
    
    new_code_cell("test_slug = 'buxoro-davlat-tibbiyot-instituti'\nyear = 2023\nform = 'kunduzgi'\nlang = 'uz'\n\ntest_url = f\"https://abt.uz/university/view?slug={test_slug}&year={year}&type={form}&lang={lang}\"\nprint(\"So'rov yuborilayotgan manzil:\", test_url)\n\nreq = requests.get(test_url, headers=HEADERS)\ntest_soup = BeautifulSoup(req.content, 'html.parser')\n\n# Jadvalni qidirish\ntables = test_soup.find_all('table')\nprint(f\"Sahifada {len(tables)} ta jadval topildi.\")"),
    
    new_markdown_cell("## 3-qadam: Jadvaldan qatorlarni (Mutaxassislik, Shifr, Grant, Kontrakt) ajratish"),
    
    new_code_cell("results = []\nif tables:\n    table = tables[0]\n    # Har bir qator (tr) ni o'qish\n    for row in table.find_all('tr')[1:]: # birinchi qator (header) ni tashlab ketamiz\n        cols = row.find_all('td')\n        if len(cols) >= 4:\n            mutaxassislik = cols[0].text.strip()\n            shifr = cols[1].text.strip()\n            grant_ball = cols[2].text.strip()\n            kontrakt_ball = cols[3].text.strip()\n            \n            results.append({\n                'Mutaxassislik': mutaxassislik,\n                'Shifr': shifr,\n                'Grant': grant_ball,\n                'Kontrakt': kontrakt_ball\n            })\n\n# DataFrame qilib ko'rsatamiz\ndf_test = pd.DataFrame(results)\ndf_test.head(10)")
])

with open('notebooks/03_abt_scraping_test.ipynb', 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Notebook 03_abt_scraping_test.ipynb yaratildi!")
