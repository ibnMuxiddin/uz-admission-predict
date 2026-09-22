import requests
from bs4 import BeautifulSoup
import re

url = 'https://oliygoh.uz/oliygohlar/buxoro-davlat-universiteti'
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.content, 'html.parser')

print("Looking for Sirtqi...")
tags = soup.find_all(string=re.compile('Sirtqi', re.IGNORECASE))
for t in tags:
    parent = t.parent
    if parent.name in ['a', 'option']:
        href = parent.get('href')
        val = parent.get('value')
        print(f'Found in {parent.name}: href={href}, value={val}')
