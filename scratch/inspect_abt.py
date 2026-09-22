import requests
from bs4 import BeautifulSoup
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

url = 'https://abt.uz/university/buxoro-davlat-tibbiyot-instituti'
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers)
soup = BeautifulSoup(r.content, 'html.parser')

print('Title:', soup.title.text if soup.title else 'No Title')

for select in soup.find_all('select'):
    print(f'Select name={select.get("name")}, id={select.get("id")}:')
    for opt in select.find_all('option'):
        print(f'  {opt.get("value")} -> {opt.text.strip()}')

for a in soup.find_all('a', href=True):
    href = a['href']
    if 'year=' in href or 'lang=' in href or 'form=' in href:
         print('Found filter link:', href, a.text.strip())

tables = soup.find_all('table')
print(f'Found {len(tables)} tables.')
if tables:
    for i, row in enumerate(tables[0].find_all('tr')):
        cols = [col.text.strip() for col in row.find_all(['th', 'td'])]
        print(f'Row {i}: {cols}')
        if i >= 5:
            break
