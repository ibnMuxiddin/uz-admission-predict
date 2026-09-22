import requests
from bs4 import BeautifulSoup
import re

url = 'https://oliygoh.uz/oliygohlar/buxoro-tibbiyot-instituti'
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.content, 'html.parser')

print('Looking for year selectors...')
years = ['2021', '2022', '2023', '2024', '2025']
for year in years:
    tags = soup.find_all(string=re.compile(year))
    for t in tags:
        parent = t.parent
        if parent.name in ['a', 'option', 'button']:
            href = parent.get('href')
            val = parent.get('value')
            print(f'Found year {year} in {parent.name}: href={href} value={val} text={parent.text.strip()}')
            if parent.parent and parent.parent.name == 'select':
                print(f'  Select name: {parent.parent.get("name")}')
