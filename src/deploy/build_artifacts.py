"""Streamlit ilovasi uchun kichik ma'lumot fayllarini tayyorlaydi.

Ilova modellarni ishga tushirmaydi: barcha guruhlar oldindan ma'lum, shuning uchun bashoratlar
08-notebookdagi kross-validatsiyadan (tasodifiy KFold, xgb_ulush) olinadi. Har bir guruhning bashorati
uni o'qitishda ko'rmagan modeldan — bu ilovada ko'rsatiladigan xatoni halol qiladi.

Ishga tushirish (loyiha ildizidan yoki istalgan joydan):
    python src/deploy/build_artifacts.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

ILDIZ = Path(__file__).resolve().parents[2]
PROCESSED = ILDIZ / 'data' / 'processed'
CHIQISH = ILDIZ / 'app' / 'data'

BOLISH = 'KFold (tasodifiy)'
MODEL = 'xgb_ulush'
# Bozordagi guruhlar shundan kam bo'lsa, xato uchun umumiy MAE olinadi
MIN_GURUH_MAE = 10


def main():
    CHIQISH.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(PROCESSED / 'model_data.csv')
    otm = pd.read_csv(PROCESSED / 'otm_prepared.csv')
    oof = pd.read_csv(PROCESSED / 'oof_bashoratlar.csv')

    # model_data otm_prepared qatorlari tartibida qurilgan (07-notebook)
    assert len(data) == len(otm) and (data['yunalish_nomi'] == otm['yunalish_nomi']).all()
    data['tuman'] = otm['tuman']

    for tur in ['grant', 'shartnoma']:
        indeks = data.index[data[f'{tur}_bali'].notna()]
        o = oof[oof['tur_bolish'] == f'{tur} | {BOLISH}'].sort_values('qator')
        assert len(o) == len(indeks)
        assert np.allclose(o['haqiqiy'].to_numpy(), data.loc[indeks, f'{tur}_bali'].to_numpy())
        data.loc[indeks, f'{tur}_bashorat'] = o[MODEL].to_numpy()

        # Bozor bo'yicha MAE — ilovada "chegarada" oralig'i uchun
        xato = (data[f'{tur}_bashorat'] - data[f'{tur}_bali']).abs()
        bozor_mae = xato.groupby(data['bozor']).agg(['mean', 'size'])
        umumiy_mae = xato.mean()
        mae = bozor_mae['mean'].where(bozor_mae['size'] >= MIN_GURUH_MAE, umumiy_mae)
        data[f'{tur}_xato'] = data['bozor'].map(mae).where(data[f'{tur}_bali'].notna())
        print(f"{tur}: {len(indeks)} guruh, umumiy MAE = {umumiy_mae:.2f}")

    guruhlar = data[['hudud', 'otm_nomi', 'yunalish_nomi', 'asosiy_yunalish', 'tuman_kvotasi', 'tuman',
                     'talim_tili', 'talim_shakli', 'fanlar_juftligi', 'bozor',
                     'grant_kvota_soni', 'shartnoma_kvota_soni',
                     'grant_bali', 'grant_bashorat', 'grant_xato',
                     'shartnoma_bali', 'shartnoma_bashorat', 'shartnoma_xato']]
    guruhlar.round(2).to_csv(CHIQISH / 'guruhlar.csv', index=False, encoding='utf-8')

    bozorlar = pd.read_csv(PROCESSED / 'bozorlar.csv')
    bozorlar.to_csv(CHIQISH / 'bozorlar.csv', index=False, encoding='utf-8')

    cv = pd.read_csv(ILDIZ / 'reports' / 'cv_natijalar.csv')
    cv.to_csv(CHIQISH / 'cv_natijalar.csv', index=False, encoding='utf-8')

    for fayl in sorted(CHIQISH.glob('*.csv')):
        print(f"{fayl.relative_to(ILDIZ)}: {fayl.stat().st_size / 1024:.0f} KB")


if __name__ == '__main__':
    main()
