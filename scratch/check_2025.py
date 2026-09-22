import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

df = pd.read_csv('data/processed/admission_combined.csv')

print("Yillar bo'yicha grant_ball va shartnoma_ball mavjudligi:")
for y in sorted(df['yil'].unique()):
    sub = df[df['yil'] == y]
    g_ok = sub['grant_ball'].notna().sum()
    s_ok = sub['shartnoma_ball'].notna().sum()
    print(f"  {y}: grant={g_ok}/{len(sub)}, shartnoma={s_ok}/{len(sub)}")

print()
t25 = df[df['yil'] == 2025]
print(f"2025 jami: {len(t25)}")
print(f"2025 grant_ball notna: {t25['grant_ball'].notna().sum()}")
print(f"2025 shartnoma_ball notna: {t25['shartnoma_ball'].notna().sum()}")
print(f"2025 is_grant_available=1: {(t25['is_grant_available']==1).sum()}")
print(f"2025 is_shartnoma_available=1: {(t25['is_shartnoma_available']==1).sum()}")

# 2025 dagi birinchi 5 qator
print()
print("2025 dagi dastlabki 5 qator:")
print(t25[['otm_nomi','grant_ball','shartnoma_ball','is_grant_available','is_shartnoma_available']].head())
