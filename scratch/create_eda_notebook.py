import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

nb = new_notebook()

nb.cells.extend([
    # ===== TITLE =====
    new_markdown_cell("# Exploratory Data Analysis (EDA)\n\nO'zbekiston OTMlariga qabul ma'lumotlari (2021–2025) bo'yicha vizual tahlil.\n\n**Ma'lumotlar manbalari:** `oliygoh.uz` → `data/processed/admission_combined.csv`"),

    # ===== SETUP =====
    new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# Grafik sozlamalari
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
sns.set_style('whitegrid')
sns.set_palette('husl')

# Figures papkasini yaratish
os.makedirs('../reports/figures', exist_ok=True)

# Ma'lumotlarni yuklash
df = pd.read_csv('../data/processed/admission_combined.csv')

# Talim shakli raqamlarini nomlarga o'zgartirish
form_map = {11: 'Kunduzgi', 12: 'Kechki', 13: 'Sirtqi', 16: 'Masofaviy'}
df['talim_shakli_nomi'] = df['talim_shakli'].map(form_map)

print(f"Ma'lumotlar yuklandi: {df.shape[0]} qator, {df.shape[1]} ustun")"""),

    # ===== 1. UMUMIY KO'RINISH =====
    new_markdown_cell("## 1. Umumiy ko'rinish"),
    new_code_cell("""print("=== Ma'lumotlar strukturasi ===")
print(df.info())
print()
print("=== Raqamli ustunlar statistikasi ===")
df.describe().round(1)"""),
    new_code_cell("""# NaN taqsimoti
nan_counts = df.isnull().sum()
nan_pct = (df.isnull().sum() / len(df) * 100).round(1)
nan_df = pd.DataFrame({'NaN soni': nan_counts, 'Foiz (%)': nan_pct})
nan_df[nan_df['NaN soni'] > 0]"""),

    # ===== 2. YILLIK TRENDLAR =====
    new_markdown_cell("## 2. Yillik trendlar — O'rtacha o'tish ballari (2021→2025)"),
    new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Grant ball trendi
grant_trend = df.groupby('yil')['grant_ball'].mean()
axes[0].plot(grant_trend.index, grant_trend.values, marker='o', linewidth=2.5, color='#2ecc71', markersize=8)
axes[0].set_title('O\\'rtacha Grant O\\'tish Bali')
axes[0].set_xlabel('Yil')
axes[0].set_ylabel('Ball')
axes[0].set_xticks(grant_trend.index)
for x, y in zip(grant_trend.index, grant_trend.values):
    axes[0].annotate(f'{y:.1f}', (x, y), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10)

# Shartnoma ball trendi
shartnoma_trend = df.groupby('yil')['shartnoma_ball'].mean()
axes[1].plot(shartnoma_trend.index, shartnoma_trend.values, marker='s', linewidth=2.5, color='#e74c3c', markersize=8)
axes[1].set_title('O\\'rtacha Shartnoma O\\'tish Bali')
axes[1].set_xlabel('Yil')
axes[1].set_ylabel('Ball')
axes[1].set_xticks(shartnoma_trend.index)
for x, y in zip(shartnoma_trend.index, shartnoma_trend.values):
    axes[1].annotate(f'{y:.1f}', (x, y), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=10)

plt.tight_layout()
plt.savefig('../reports/figures/01_yillik_trendlar.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saqlandi: reports/figures/01_yillik_trendlar.png")"""),

    # ===== 3. OTM REYTINGI =====
    new_markdown_cell("## 3. OTMlar reytingi — Eng raqobatli va eng oson Top-10"),
    new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Eng raqobatli (grant ball yuqori)
top10 = df.groupby('otm_nomi')['grant_ball'].mean().dropna().sort_values(ascending=False).head(10)
top10_short = [n[:40] + '...' if len(n) > 40 else n for n in top10.index]
axes[0].barh(top10_short[::-1], top10.values[::-1], color=sns.color_palette('Reds_r', 10))
axes[0].set_title('Eng raqobatli 10 OTM (Grant Ball)')
axes[0].set_xlabel('O\\'rtacha Grant Ball')
for i, v in enumerate(top10.values[::-1]):
    axes[0].text(v + 0.5, i, f'{v:.1f}', va='center', fontsize=9)

# Eng oson (grant ball past)
bottom10 = df.groupby('otm_nomi')['grant_ball'].mean().dropna().sort_values(ascending=True).head(10)
bottom10_short = [n[:40] + '...' if len(n) > 40 else n for n in bottom10.index]
axes[1].barh(bottom10_short[::-1], bottom10.values[::-1], color=sns.color_palette('Greens', 10))
axes[1].set_title('Eng oson 10 OTM (Grant Ball)')
axes[1].set_xlabel('O\\'rtacha Grant Ball')
for i, v in enumerate(bottom10.values[::-1]):
    axes[1].text(v + 0.5, i, f'{v:.1f}', va='center', fontsize=9)

plt.tight_layout()
plt.savefig('../reports/figures/02_otm_reytingi.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saqlandi: reports/figures/02_otm_reytingi.png")"""),

    # ===== 4. TA'LIM SHAKLI =====
    new_markdown_cell("## 4. Ta'lim shakli bo'yicha ballar taqsimoti"),
    new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

colors = {'Kunduzgi': '#3498db', 'Kechki': '#e67e22', 'Sirtqi': '#2ecc71', 'Masofaviy': '#9b59b6'}

sns.boxplot(data=df, x='talim_shakli_nomi', y='grant_ball', ax=axes[0],
            order=['Kunduzgi', 'Kechki', 'Sirtqi', 'Masofaviy'], palette=colors)
axes[0].set_title('Grant Ball taqsimoti (Ta\\'lim shakli bo\\'yicha)')
axes[0].set_xlabel('Ta\\'lim shakli')
axes[0].set_ylabel('Grant Ball')

sns.boxplot(data=df, x='talim_shakli_nomi', y='shartnoma_ball', ax=axes[1],
            order=['Kunduzgi', 'Kechki', 'Sirtqi', 'Masofaviy'], palette=colors)
axes[1].set_title('Shartnoma Ball taqsimoti (Ta\\'lim shakli bo\\'yicha)')
axes[1].set_xlabel('Ta\\'lim shakli')
axes[1].set_ylabel('Shartnoma Ball')

plt.tight_layout()
plt.savefig('../reports/figures/03_talim_shakli.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saqlandi: reports/figures/03_talim_shakli.png")"""),

    # ===== 5. TA'LIM TILI =====
    new_markdown_cell("## 5. Ta'lim tili bo'yicha raqobat farqi"),
    new_code_cell("""lang_map = {'uz': "O'zbek", 'ru': 'Rus', 'kk': 'Qoraqalpoq'}
df['talim_tili_nomi'] = df['talim_tili'].map(lang_map)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

sns.boxplot(data=df, x='talim_tili_nomi', y='grant_ball', ax=axes[0],
            palette='Set2', order=["O'zbek", 'Rus', 'Qoraqalpoq'])
axes[0].set_title('Grant Ball (Til bo\\'yicha)')
axes[0].set_xlabel('Ta\\'lim tili')
axes[0].set_ylabel('Grant Ball')

sns.boxplot(data=df, x='talim_tili_nomi', y='shartnoma_ball', ax=axes[1],
            palette='Set2', order=["O'zbek", 'Rus', 'Qoraqalpoq'])
axes[1].set_title('Shartnoma Ball (Til bo\\'yicha)')
axes[1].set_xlabel('Ta\\'lim tili')
axes[1].set_ylabel('Shartnoma Ball')

plt.tight_layout()
plt.savefig('../reports/figures/04_talim_tili.png', dpi=150, bbox_inches='tight')
plt.show()
print("Saqlandi: reports/figures/04_talim_tili.png")"""),

    # ===== 6. KVOTA VA BALL KORRELYATSIYASI =====
    new_markdown_cell("## 6. Kvota va Ball korrelyatsiyasi\n\nKvota kam bo'lganda ball yuqori bo'ladimi?"),
    new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Grant kvota vs Grant ball
mask_g = (df['grant_kvota'] > 0) & (df['grant_ball'].notna())
axes[0].scatter(df.loc[mask_g, 'grant_kvota'], df.loc[mask_g, 'grant_ball'], alpha=0.3, s=10, color='#2ecc71')
axes[0].set_title('Grant Kvota vs Grant Ball')
axes[0].set_xlabel('Grant Kvota (joy soni)')
axes[0].set_ylabel('Grant Ball')
axes[0].set_xlim(0, df.loc[mask_g, 'grant_kvota'].quantile(0.95))

# Shartnoma kvota vs Shartnoma ball
mask_s = (df['shartnoma_kvota'] > 0) & (df['shartnoma_ball'].notna())
axes[1].scatter(df.loc[mask_s, 'shartnoma_kvota'], df.loc[mask_s, 'shartnoma_ball'], alpha=0.3, s=10, color='#e74c3c')
axes[1].set_title('Shartnoma Kvota vs Shartnoma Ball')
axes[1].set_xlabel('Shartnoma Kvota (joy soni)')
axes[1].set_ylabel('Shartnoma Ball')
axes[1].set_xlim(0, df.loc[mask_s, 'shartnoma_kvota'].quantile(0.95))

plt.tight_layout()
plt.savefig('../reports/figures/05_kvota_ball_korr.png', dpi=150, bbox_inches='tight')
plt.show()

# Korrelyatsiya koeffitsiyentlari
corr_g = df.loc[mask_g, ['grant_kvota', 'grant_ball']].corr().iloc[0, 1]
corr_s = df.loc[mask_s, ['shartnoma_kvota', 'shartnoma_ball']].corr().iloc[0, 1]
print(f"Grant kvota <-> Grant ball korrelyatsiyasi: {corr_g:.3f}")
print(f"Shartnoma kvota <-> Shartnoma ball korrelyatsiyasi: {corr_s:.3f}")
print("Saqlandi: reports/figures/05_kvota_ball_korr.png")"""),

    # ===== 7. GRANT VS SHARTNOMA MAVJUDLIGI =====
    new_markdown_cell("## 7. Grant vs Shartnoma mavjudligi\n\nYo'nalishlarning qancha foizi faqat grant, faqat shartnoma yoki ikkalasida ham qabul qiladi?"),
    new_code_cell("""# Kategoriyalar
both = ((df['is_grant_available'] == 1) & (df['is_shartnoma_available'] == 1)).sum()
only_grant = ((df['is_grant_available'] == 1) & (df['is_shartnoma_available'] == 0)).sum()
only_shartnoma = ((df['is_grant_available'] == 0) & (df['is_shartnoma_available'] == 1)).sum()

labels = ['Grant + Shartnoma', 'Faqat Grant', 'Faqat Shartnoma']
sizes = [both, only_grant, only_shartnoma]
colors_pie = ['#3498db', '#2ecc71', '#e74c3c']
explode = (0.03, 0.03, 0.03)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Pie chart
axes[0].pie(sizes, labels=labels, colors=colors_pie, explode=explode,
           autopct='%1.1f%%', startangle=90, textprops={'fontsize': 11})
axes[0].set_title("Qabul turi bo'yicha yo'nalishlar taqsimoti")

# Yillar bo'yicha trend
yearly = df.groupby('yil').agg(
    grant_pct=('is_grant_available', 'mean'),
    shartnoma_pct=('is_shartnoma_available', 'mean')
).reset_index()
yearly['grant_pct'] *= 100
yearly['shartnoma_pct'] *= 100

axes[1].plot(yearly['yil'], yearly['grant_pct'], marker='o', label='Grant mavjud (%)', color='#2ecc71', linewidth=2)
axes[1].plot(yearly['yil'], yearly['shartnoma_pct'], marker='s', label='Shartnoma mavjud (%)', color='#e74c3c', linewidth=2)
axes[1].set_title("Yillar bo'yicha Grant/Shartnoma mavjudligi")
axes[1].set_xlabel('Yil')
axes[1].set_ylabel('Foiz (%)')
axes[1].legend()
axes[1].set_xticks(yearly['yil'])

plt.tight_layout()
plt.savefig('../reports/figures/06_grant_shartnoma.png', dpi=150, bbox_inches='tight')
plt.show()
print(f"Grant + Shartnoma: {both} ({both/len(df)*100:.1f}%)")
print(f"Faqat Grant: {only_grant} ({only_grant/len(df)*100:.1f}%)")
print(f"Faqat Shartnoma: {only_shartnoma} ({only_shartnoma/len(df)*100:.1f}%)")
print("Saqlandi: reports/figures/06_grant_shartnoma.png")"""),

    # ===== XULOSA =====
    new_markdown_cell("## Xulosa\n\nEDA bo'yicha topilgan asosiy insaytlar yuqoridagi grafiklarda aks ettirildi. Barcha rasmlar `reports/figures/` papkasiga saqlandi. Keyingi qadam — Feature Engineering va ML Model qurish.")
])

with open('notebooks/04_eda.ipynb', 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Notebook 04_eda.ipynb muvaffaqiyatli yaratildi!")
