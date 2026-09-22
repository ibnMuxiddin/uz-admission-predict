import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import time
import csv
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Server xatoliklarini oldini olish uchun (Retry) sozlamalari
session = requests.Session()
retry = Retry(connect=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)

base_url = 'https://mandat.uzbmb.uz/Mandat2025'

def main():
    # Fayl saqlanadigan katalogni aniqlash (uz-admission-predict/data/raw)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    output_dir = os.path.join(project_root, 'data', 'raw')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'abiturents.csv')
    
    file_exists = os.path.isfile(output_file)
    
    print(f"Ma'lumotlar saqlanadigan fayl: {output_file}")
    print("Yuklash jarayoni boshlandi. (Jarayonni to'xtatish uchun Ctrl+C bosing)\n")
    
    # Faylni Append (qo'shib borish) rejimida ochamiz. Shunda uzilish bo'lsa, davom etaveradi.
    with open(output_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Agar fayl endi yaratilayotgan bo'lsa, ustun nomlarini yozamiz
        if not file_exists:
            writer.writerow(['ismi', 'ID', 'otm_nomi', 'yonalishi', 'shifr_kodi', 'talim_tili', 'talim_shakli', 'toplagan_bali'])
            completed_groups = set()
        else:
            print("Oldingi ma'lumotlar o'qilmoqda (resume)...")
            import pandas as pd
            try:
                df = pd.read_csv(output_file, usecols=['otm_nomi', 'yonalishi', 'talim_tili', 'talim_shakli'])
                df.drop_duplicates(inplace=True)
                completed_groups = set([tuple(x) for x in df.values])
                # Oxirgi guruh chala qolgan bo'lishi mumkin, shuning uchun uni qayta yuklaymiz
                if len(df) > 0:
                    last_group = tuple(df.values[-1])
                    if last_group in completed_groups:
                        completed_groups.remove(last_group)
                print(f"{len(completed_groups)} ta yo'nalish allaqachon yuklangan, ular tashlab o'tiladi.")
            except Exception as e:
                print("CSV o'qishda xatolik, noldan boshlanadi:", e)
                completed_groups = set()

        print("Hududlar yuklanmoqda...")
        regions = session.get(f'{base_url}/GetRegions/', params={'lang': 'uz'}).json()
        
        for reg in regions:
            region_id = reg['region_id']
            region_name = reg['region_name']
            print(f"\n======================================")
            print(f"HUDUD: {region_name} (ID: {region_id})")
            print(f"======================================")
            
            try:
                universities = session.get(f'{base_url}/GetUniversitiesByRegion/', params={'lang': 'uz', 'regionid': region_id}, timeout=15).json()
            except Exception as e:
                print(f"OTMlarni yuklashda xatolik ({region_name}): {e}")
                continue
            
            for uni in universities:
                univer_id = uni['universityId']
                otm_nomi = uni['universityName']
                print(f"\n  -> OTM: {otm_nomi}")
                
                try:
                    faculties = session.get(f'{base_url}/GetFacultiesByUniversity/', params={'lang': 'uz', 'universityid': univer_id}, timeout=15).json()
                except Exception as e:
                    print(f"  -> Yo'nalishlarni yuklashda xatolik ({otm_nomi}): {e}")
                    continue
                    
                for fac in faculties:
                    faculty_id = fac['mvdir']
                    yunalish_nomi = fac['facultyname']
                    
                    try:
                        langs = session.get(f'{base_url}/GetEdlangsByMvdir/', params={'mvdir': faculty_id, 'universityid': univer_id}, timeout=15).json()
                    except Exception as e:
                        continue
                        
                    for lng in langs:
                        edlang_id = lng['educlangid']
                        talim_tili = lng['educlanguage']
                        
                        try:
                            types = session.get(f'{base_url}/GetEdTypesByMvdirEdLang/', params={'lang': 'uz', 'universityid': univer_id, 'mvdir': faculty_id, 'educlangid': edlang_id}, timeout=15).json()
                        except Exception as e:
                            continue
                            
                        for typ in types:
                            edtype_id = typ['eductypeId']
                            talim_shakli = typ['eductype']
                            
                            group_tuple = (otm_nomi, yunalish_nomi, talim_tili, talim_shakli)
                            if group_tuple in completed_groups:
                                # print(f"      Tashlab o'tildi (allaqachon bor): {yunalish_nomi} | {talim_tili} | {talim_shakli}")
                                continue
                            
                            print(f"      {yunalish_nomi} | {talim_tili} | {talim_shakli} ...")
                            
                            page = 1
                            while True:
                                params = {
                                    'pageNumber': page, 'pageSize': 100,
                                    'region': region_id, 'univer': univer_id,
                                    'faculty': faculty_id, 'edlang': edlang_id, 'edtype': edtype_id
                                }
                                
                                try_count = 0
                                while try_count < 5:
                                    try:
                                        r = session.get(f'{base_url}/Paginate', params=params, timeout=15)
                                        soup = BeautifulSoup(r.text, 'html.parser')
                                        candidates = soup.find_all('div', class_='m3-rank-item')
                                        break
                                    except Exception as e:
                                        try_count += 1
                                        print(f"      Sahifa {page} da xatolik. 2 soniya kutib qayta urinamiz... (Urinish: {try_count}/5)")
                                        time.sleep(2)
                                
                                if try_count == 5:
                                    print(f"      Sahifa {page} ni yuklab bo'lmadi. Keyingisiga o'tilmoqda.")
                                    break
                                
                                if not candidates:
                                    break
                                
                                rows_to_write = []
                                for c in candidates:
                                    name_tag = c.find('p', class_='m3-rank-name')
                                    ismi = name_tag.text.strip() if name_tag else ""
                                    
                                    id_tag = c.find('p', class_='m3-rank-id')
                                    ab_id = id_tag.find('b').text.strip() if id_tag and id_tag.find('b') else ""
                                    
                                    score_tag = c.find('div', class_='m3-rank-score')
                                    if score_tag and score_tag.find('b'):
                                        score_text = score_tag.find('b').text.strip().replace(',', '.')
                                        try:
                                            score = float(score_text)
                                        except ValueError:
                                            score = 0.0
                                    else:
                                        score = 0.0
                                    
                                    rows_to_write.append([ismi, ab_id, otm_nomi, yunalish_nomi, faculty_id, talim_tili, talim_shakli, score])
                                
                                # Yig'ilgan ma'lumotni darhol CSV faylga yozish
                                writer.writerows(rows_to_write)
                                f.flush() # OS dan diskka yozishni talab qiladi (yo'qolib qolmasligi uchun)
                                
                                page += 1
                                
                            # Sayt serverini qulamasligi uchun juda qisqa tanaffus
                            time.sleep(0.3)

if __name__ == '__main__':
    main()
