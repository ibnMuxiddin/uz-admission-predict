import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

r = requests.get('https://dtm.uz/page/stat_tahlil', headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
soup = BeautifulSoup(r.content, 'html.parser')

print("=== Yuklab olinadigan fayllar ===")
for a in soup.find_all('a', href=True):
    href = a.get('href')
    text = a.text.strip()
    if href and ('.pdf' in href or '.xlsx' in href or '.xls' in href or '.csv' in href or 'upload' in href or 'file' in href):
        print(f'{text} -> {href}')

print("\n=== Iframes ===")
for iframe in soup.find_all('iframe'):
    print(f'iframe src: {iframe.get("src")}')

print("\n=== Rasmlar (infografiklar) ===")
for img in soup.find_all('img'):
    src = img.get('src', '')
    if 'stat' in src.lower() or 'tahlil' in src.lower() or 'upload' in src.lower():
        print(f'Image: {src}')

print("\n=== Barcha sahifa matni ===")
body = soup.find('body')
if body:
    text = body.get_text(separator='\n', strip=True)
    for line in text.split('\n'):
        if line.strip():
            print(line.strip())
