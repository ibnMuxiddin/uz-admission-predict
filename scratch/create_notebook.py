import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

nb = new_notebook()

nb.cells.extend([
    new_markdown_cell("# Data Cleaning va Bo'sh Qiymatlarni (Missing Values) Tahlil Qilish\n\nUshbu noutbukda biz `data_processing.py` dan chiqqan to'liq ma'lumotlarni o'qiymiz va qaysi qatorlarda bo'sh qiymatlar (NaN) borligini aniqlaymiz."),
    new_code_cell("import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\nimport seaborn as sns\n\n# Grafiklar uchun sozlamalar\nplt.style.use('seaborn-v0_8-whitegrid')\nsns.set_palette('pastel')"),
    new_markdown_cell("## 1. Ma'lumotlarni yuklash"),
    new_code_cell("df = pd.read_csv('../data/processed/admission_combined.csv')\ndf.head()"),
    new_markdown_cell("## 2. Bo'sh qiymatlar statistikasi\nKeling, qaysi ustunlarda qancha bo'sh (NaN) borligini ko'ramiz."),
    new_code_cell("missing_stats = df.isnull().sum()\nmissing_percent = (df.isnull().sum() / len(df)) * 100\n\nmissing_df = pd.DataFrame({'Missing Values': missing_stats, 'Percentage (%)': missing_percent})\nmissing_df = missing_df[missing_df['Missing Values'] > 0]\nmissing_df"),
    new_markdown_cell("## 3. OTM va Yillar bo'yicha bo'sh qiymatlar\nEng ko'p qaysi yilda va qaysi universitetda ma'lumot yetishmasligini tekshiramiz."),
    new_code_cell("# Faqat grant balli yoki shartnoma balli yo'q bo'lgan qatorlarni ajratib olamiz\nmissing_scores = df[df['grant_ball'].isnull() | df['shartnoma_ball'].isnull()]\n\nprint(f\"Jami {len(missing_scores)} ta qatorda o'tish ballari mavjud emas.\")"),
    new_code_cell("# Yillar kesimida\nmissing_scores.groupby('yil').size().plot(kind='bar', color='salmon')\nplt.title('Yillar bo\\'yicha ballari yo\\'q yo\\'nalishlar soni')\nplt.ylabel('Soni')\nplt.show()"),
    new_code_cell("# Eng ko'p ballari yo'q bo'lgan OTMlar (Top 10)\nmissing_scores.groupby('otm_nomi').size().sort_values(ascending=False).head(10)"),
    new_markdown_cell("## 4. Aniq qatorlarni ko'rish\nEndi siz o'zingiz bu qatorlarni ko'rib, kerakli tashqi manbalardan izlashingiz mumkin. Masalan, 2025 yildagi bo'sh qatorlar:"),
    new_code_cell("missing_scores[missing_scores['yil'] == 2025].head(15)")
])

with open('notebooks/02_data_cleaning.ipynb', 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Notebook muvaffaqiyatli yaratildi!")
