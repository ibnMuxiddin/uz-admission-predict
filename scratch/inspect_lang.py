import requests
from bs4 import BeautifulSoup

for lang in ['uz', 'ru']:
    url = f'https://oliygoh.uz/oliygohlar/buxoro-tibbiyot-instituti/2023?lang={lang}'
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, 'html.parser')
    table_div = soup.find('div', class_='table')
    if table_div:
        rows = table_div.find_all('div', class_='tr')
        print(f'Lang {lang}: Found {len(rows)-1} rows')
        if len(rows) > 1:
            cols = rows[1].find_all('div', class_='td')
            print(f' First row Col 0: {" ".join(cols[0].text.split())}')
