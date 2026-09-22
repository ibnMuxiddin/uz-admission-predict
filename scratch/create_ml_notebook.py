import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

nb = new_notebook()

nb.cells.extend([
    new_markdown_cell("# Feature Engineering + ML Model\n\n**Maqsad:** O'tish ballarini bashorat qilish (XGBoost)\n\n- **Grant modeli:** Train=2021-2023, Test=2024 (2025 da grant ma'lumoti yo'q)\n- **Shartnoma modeli:** Train=2021-2024, Test=2025"),

    # ===== SETUP =====
    new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')
import os
os.makedirs('../reports/figures', exist_ok=True)

df = pd.read_csv('../data/processed/admission_combined.csv')

# Keraksiz ustunlarni tashlash
df = df.drop(columns=['yo_nalish_kodi', 'mutaxassislik'])
print(f"Jami: {len(df)} qator, Ustunlar: {df.columns.tolist()}")"""),

    # ===== FEATURE ENGINEERING =====
    new_markdown_cell("## 1. Feature Engineering"),
    new_code_cell("""# Label Encoding
le_tili = LabelEncoder()
le_shakli = LabelEncoder()
df['talim_tili_enc'] = le_tili.fit_transform(df['talim_tili'])
df['talim_shakli_enc'] = le_shakli.fit_transform(df['talim_shakli'].astype(str))

print("Til:", dict(zip(le_tili.classes_, le_tili.transform(le_tili.classes_))))
print("Shakl:", dict(zip(le_shakli.classes_, le_shakli.transform(le_shakli.classes_))))"""),

    new_code_cell("""# Target Encoding: otm_nomi (faqat train datadan)
# Grant uchun: train = 2021-2023
otm_g_mean = df[df['yil'] <= 2023].groupby('otm_nomi')['grant_ball'].mean()
df['otm_grant_enc'] = df['otm_nomi'].map(otm_g_mean)
df['otm_grant_enc'] = df['otm_grant_enc'].fillna(df[df['yil'] <= 2023]['grant_ball'].mean())

# Shartnoma uchun: train = 2021-2024
otm_s_mean = df[df['yil'] <= 2024].groupby('otm_nomi')['shartnoma_ball'].mean()
df['otm_shartnoma_enc'] = df['otm_nomi'].map(otm_s_mean)
df['otm_shartnoma_enc'] = df['otm_shartnoma_enc'].fillna(df[df['yil'] <= 2024]['shartnoma_ball'].mean())

print("Target Encoding tayyor.")"""),

    # ===== FEATURES =====
    new_code_cell("""features_grant = [
    'yil', 'talim_tili_enc', 'talim_shakli_enc',
    'jami_kvota', 'grant_kvota', 'shartnoma_kvota',
    'is_grant_available', 'is_shartnoma_available',
    'otm_grant_enc'
]

features_shartnoma = [
    'yil', 'talim_tili_enc', 'talim_shakli_enc',
    'jami_kvota', 'grant_kvota', 'shartnoma_kvota',
    'is_grant_available', 'is_shartnoma_available',
    'otm_shartnoma_enc'
]

print("Feature ro'yxatlari tayyor.")"""),

    # ===== GRANT MODEL =====
    new_markdown_cell("## 2. Grant Ball Modeli\n\nTrain: 2021-2023, Test: 2024 (2025 da grant ma'lumoti yo'q)"),
    new_code_cell("""# Grant mavjud va balli bor qatorlar
train_g = df[(df['yil'] <= 2023) & (df['is_grant_available'] == 1)].dropna(subset=['grant_ball'])
test_g = df[(df['yil'] == 2024) & (df['is_grant_available'] == 1)].dropna(subset=['grant_ball'])

X_train_g, y_train_g = train_g[features_grant], train_g['grant_ball']
X_test_g, y_test_g = test_g[features_grant], test_g['grant_ball']
print(f"Grant Train: {len(X_train_g)}, Grant Test: {len(X_test_g)}")

model_grant = xgb.XGBRegressor(
    n_estimators=300, max_depth=6, learning_rate=0.1,
    subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1
)
model_grant.fit(X_train_g, y_train_g, eval_set=[(X_test_g, y_test_g)], verbose=False)

y_pred_g = model_grant.predict(X_test_g)
mae_g = mean_absolute_error(y_test_g, y_pred_g)
rmse_g = np.sqrt(mean_squared_error(y_test_g, y_pred_g))
r2_g = r2_score(y_test_g, y_pred_g)

print(f"\\n=== Grant Ball Natijalari ===")
print(f"MAE:  {mae_g:.2f} ball")
print(f"RMSE: {rmse_g:.2f} ball")
print(f"R²:   {r2_g:.4f} ({r2_g*100:.1f}%)")"""),

    # ===== SHARTNOMA MODEL =====
    new_markdown_cell("## 3. Shartnoma Ball Modeli\n\nTrain: 2021-2024, Test: 2025"),
    new_code_cell("""train_s = df[(df['yil'] <= 2024) & (df['is_shartnoma_available'] == 1)].dropna(subset=['shartnoma_ball'])
test_s = df[(df['yil'] == 2025) & (df['is_shartnoma_available'] == 1)].dropna(subset=['shartnoma_ball'])

X_train_s, y_train_s = train_s[features_shartnoma], train_s['shartnoma_ball']
X_test_s, y_test_s = test_s[features_shartnoma], test_s['shartnoma_ball']
print(f"Shartnoma Train: {len(X_train_s)}, Shartnoma Test: {len(X_test_s)}")

model_shartnoma = xgb.XGBRegressor(
    n_estimators=300, max_depth=6, learning_rate=0.1,
    subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1
)
model_shartnoma.fit(X_train_s, y_train_s, eval_set=[(X_test_s, y_test_s)], verbose=False)

y_pred_s = model_shartnoma.predict(X_test_s)
mae_s = mean_absolute_error(y_test_s, y_pred_s)
rmse_s = np.sqrt(mean_squared_error(y_test_s, y_pred_s))
r2_s = r2_score(y_test_s, y_pred_s)

print(f"\\n=== Shartnoma Ball Natijalari ===")
print(f"MAE:  {mae_s:.2f} ball")
print(f"RMSE: {rmse_s:.2f} ball")
print(f"R²:   {r2_s:.4f} ({r2_s*100:.1f}%)")"""),

    # ===== FEATURE IMPORTANCE =====
    new_markdown_cell("## 4. Feature Importance"),
    new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

feat_g = pd.Series(model_grant.feature_importances_, index=features_grant).sort_values()
feat_g.plot(kind='barh', ax=axes[0], color='#2ecc71')
axes[0].set_title('Grant Ball — Feature Importance')

feat_s = pd.Series(model_shartnoma.feature_importances_, index=features_shartnoma).sort_values()
feat_s.plot(kind='barh', ax=axes[1], color='#e74c3c')
axes[1].set_title('Shartnoma Ball — Feature Importance')

plt.tight_layout()
plt.savefig('../reports/figures/07_feature_importance.png', dpi=150, bbox_inches='tight')
plt.show()"""),

    # ===== ACTUAL VS PREDICTED =====
    new_markdown_cell("## 5. Haqiqiy vs Bashorat"),
    new_code_cell("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].scatter(y_test_g, y_pred_g, alpha=0.3, s=10, color='#2ecc71')
lim_g = [min(y_test_g.min(), y_pred_g.min()), max(y_test_g.max(), y_pred_g.max())]
axes[0].plot(lim_g, lim_g, 'r--', linewidth=2)
axes[0].set_xlabel('Haqiqiy')
axes[0].set_ylabel('Bashorat')
axes[0].set_title(f'Grant Ball 2024 (R²={r2_g:.3f}, MAE={mae_g:.1f})')

axes[1].scatter(y_test_s, y_pred_s, alpha=0.3, s=10, color='#e74c3c')
lim_s = [min(y_test_s.min(), y_pred_s.min()), max(y_test_s.max(), y_pred_s.max())]
axes[1].plot(lim_s, lim_s, 'r--', linewidth=2)
axes[1].set_xlabel('Haqiqiy')
axes[1].set_ylabel('Bashorat')
axes[1].set_title(f'Shartnoma Ball 2025 (R²={r2_s:.3f}, MAE={mae_s:.1f})')

plt.tight_layout()
plt.savefig('../reports/figures/08_haqiqiy_vs_bashorat.png', dpi=150, bbox_inches='tight')
plt.show()"""),

    # ===== XULOSA =====
    new_markdown_cell("## 6. Yakuniy Xulosa"),
    new_code_cell("""print("=" * 50)
print("YAKUNIY NATIJALAR")
print("=" * 50)
print(f"\\nGrant Ball (2024 test):")
print(f"  MAE:  {mae_g:.2f} ball xatolik")
print(f"  R²:   {r2_g*100:.1f}% aniqlik")
print(f"  Test:  {len(X_test_g)} qator")
print(f"\\nShartnoma Ball (2025 test):")
print(f"  MAE:  {mae_s:.2f} ball xatolik")
print(f"  R²:   {r2_s*100:.1f}% aniqlik")
print(f"  Test:  {len(X_test_s)} qator")""")
])

with open('notebooks/05_ml_model.ipynb', 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)
print("Notebook 05_ml_model.ipynb qayta yaratildi!")
