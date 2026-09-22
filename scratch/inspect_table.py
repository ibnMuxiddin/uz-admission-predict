import requests
from bs4 import BeautifulSoup

for y in ['2025', '2024']:
    url = f'https://oliygoh.uz/oliygohlar/buxoro-tibbiyot-instituti/{y}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser')

    table_div = soup.find('div', class_='table')
    print(f'=== YEAR {y} ===')
    if table_div:
        rows = table_div.find_all('div', class_='tr')
        if len(rows) > 1:
            cols = rows[1].find_all('div', class_='td')
            for j, col in enumerate(cols):
                print(f'Col {j}: {" ".join(col.text.split())}')
