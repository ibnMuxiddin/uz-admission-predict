"""OTM o'tish ballari bashorati — Streamlit ilovasi.

Ma'lumotlar `app/data/` da (`src/deploy/build_artifacts.py` tayyorlaydi). Ishga tushirish:
    streamlit run app/streamlit_app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).parent / 'data'

st.set_page_config(page_title="OTM o'tish ballari bashorati", page_icon='🎓', layout='wide')

OGOHLANTIRISH = (
    "Bashoratlar **2026** yilgi qabul ma'lumotlari asosida qurilgan modeldan. Har bir yo'nalishning bashorati "
    "shu yo'nalishni o'qitishda ko'rmagan modeldan olingan (kross-validatsiya). Bu rasmiy natija emas — "
    "yakuniy qaror uchun mandat.uzbmb.uz ma'lumotlariga tayaning."
)


@st.cache_data
def yukla():
    guruhlar = pd.read_csv(DATA / 'guruhlar.csv')
    bozorlar = pd.read_csv(DATA / 'bozorlar.csv')
    cv = pd.read_csv(DATA / 'cv_natijalar.csv')
    return guruhlar, bozorlar, cv


def holat(ball, bashorat, xato):
    """Abituriyent bali bashoratdan qanchalik uzoq — bozordagi o'rtacha xato (MAE) bilan solishtiriladi."""
    if pd.isna(bashorat):
        return None
    farq = ball - bashorat
    if farq >= xato:
        return '🟢 Yuqori'
    if farq > -xato:
        return '🟡 Chegarada'
    return '🔴 Past'


def abituriyent_sahifasi():
    guruhlar, bozorlar, _ = yukla()
    st.title('🎓 Qaysi yo\'nalishlarga kira olaman?')
    st.caption(OGOHLANTIRISH)

    c1, c2 = st.columns([2, 1])
    juftlik = c1.selectbox('Imtihon fanlaringiz (1-fan + 2-fan)', sorted(bozorlar['fanlar_juftligi']))
    ball = c2.number_input("To'plagan balingiz", min_value=56.7, max_value=220.0, value=150.0, step=0.1)

    bozor = bozorlar.loc[bozorlar['fanlar_juftligi'] == juftlik, 'bozor'].iloc[0]
    bozor_juftliklari = sorted(bozorlar.loc[bozorlar['bozor'] == bozor, 'fanlar_juftligi'])
    if len(bozor_juftliklari) > 1:
        st.info('Bu fanlar bilan quyidagi juftlikdagi yo\'nalishlarda ham qatnashasiz: '
                + ', '.join(f'`{j}`' for j in bozor_juftliklari))

    d = guruhlar[guruhlar['bozor'] == bozor].copy()

    with st.expander('Filtrlar', expanded=True):
        f1, f2, f3, f4 = st.columns(4)
        hudud = f1.multiselect('Hudud', sorted(d['hudud'].unique()))
        shakl = f2.multiselect("Ta'lim shakli", sorted(d['talim_shakli'].unique()))
        til = f3.multiselect("Ta'lim tili", sorted(d['talim_tili'].unique()))
        tur = f4.radio("O'rin turi", ['Grant', 'Shartnoma'], horizontal=True)
        faqat_kira_oladi = st.checkbox("Faqat 🟢 va 🟡 holatlarni ko'rsatish", value=True)

    if hudud:
        d = d[d['hudud'].isin(hudud)]
    if shakl:
        d = d[d['talim_shakli'].isin(shakl)]
    if til:
        d = d[d['talim_tili'].isin(til)]

    t = tur.lower()
    d = d[d[f'{t}_kvota_soni'] > 0].copy()
    d['holat'] = [holat(ball, b, x) for b, x in zip(d[f'{t}_bashorat'], d[f'{t}_xato'])]
    d['farq'] = (ball - d[f'{t}_bashorat']).round(1)
    if faqat_kira_oladi:
        d = d[d['holat'].isin(['🟢 Yuqori', '🟡 Chegarada'])]
    d = d.sort_values(f'{t}_bashorat', ascending=False)

    m1, m2, m3 = st.columns(3)
    m1.metric('Yo\'nalishlar', len(d))
    m2.metric('🟢 Yuqori', int((d['holat'] == '🟢 Yuqori').sum()))
    m3.metric('🟡 Chegarada', int((d['holat'] == '🟡 Chegarada').sum()))

    st.dataframe(
        d[['holat', 'otm_nomi', 'yunalish_nomi', 'talim_tili', 'talim_shakli', 'hudud',
           f'{t}_kvota_soni', f'{t}_bashorat', 'farq', f'{t}_xato', f'{t}_bali']],
        hide_index=True, width='stretch',
        column_config={
            'holat': 'Holat',
            'otm_nomi': 'OTM',
            'yunalish_nomi': "Yo'nalish",
            'talim_tili': 'Til',
            'talim_shakli': 'Shakl',
            'hudud': 'Hudud',
            f'{t}_kvota_soni': st.column_config.NumberColumn('Kvota', format='%d'),
            f'{t}_bashorat': st.column_config.NumberColumn('Bashorat', format='%.1f'),
            'farq': st.column_config.NumberColumn('Balingiz − bashorat', format='%+.1f'),
            f'{t}_xato': st.column_config.NumberColumn('± o\'rtacha xato', format='%.1f'),
            f'{t}_bali': st.column_config.NumberColumn('2026 haqiqiy', format='%.1f'),
        },
    )
    st.caption("**Holat:** 🟢 — balingiz bashoratdan kamida bir o'rtacha xato yuqori; 🟡 — bashoratga bir "
               "o'rtacha xato oralig'ida yaqin; 🔴 — undan past. O'rtacha xato — shu bozordagi yo'nalishlar "
               "bo'yicha modelning o'rtacha adashishi. Bu ehtimollik emas, taxminiy yo'l-yo'riq.")


def yunalish_sahifasi():
    guruhlar, bozorlar, _ = yukla()
    st.title("📍 Yo'nalish bo'yicha bashorat")
    st.caption(OGOHLANTIRISH)

    c1, c2 = st.columns(2)
    otm = c1.selectbox('OTM', sorted(guruhlar['otm_nomi'].unique()))
    d = guruhlar[guruhlar['otm_nomi'] == otm]
    yunalish = c2.selectbox("Yo'nalish", sorted(d['yunalish_nomi'].unique()))
    d = d[d['yunalish_nomi'] == yunalish]
    c3, c4 = st.columns(2)
    til = c3.selectbox("Ta'lim tili", sorted(d['talim_tili'].unique()))
    d = d[d['talim_tili'] == til]
    shakl = c4.selectbox("Ta'lim shakli", sorted(d['talim_shakli'].unique()))
    g = d[d['talim_shakli'] == shakl].iloc[0]

    st.markdown(f"**Fanlar:** {g['fanlar_juftligi']}  ·  **Hudud:** {g['hudud']}"
                + (f"  ·  **Tuman kvotasi:** {g['tuman']}" if g['tuman_kvotasi'] else ''))

    for tur, nom in [('grant', 'Grant'), ('shartnoma', "To'lov-shartnoma")]:
        st.subheader(nom)
        if g[f'{tur}_kvota_soni'] == 0:
            st.write('Bu guruhda bu turdagi o\'rin yo\'q.')
            continue
        k1, k2, k3, k4 = st.columns(4)
        k1.metric('Kvota', int(g[f'{tur}_kvota_soni']))
        k2.metric('Bashorat', f"{g[f'{tur}_bashorat']:.1f}")
        k3.metric('2026 haqiqiy', f"{g[f'{tur}_bali']:.1f}",
                  delta=f"{g[f'{tur}_bali'] - g[f'{tur}_bashorat']:+.1f} bashoratdan", delta_color='off')
        k4.metric("Bozordagi o'rtacha xato", f"± {g[f'{tur}_xato']:.1f}")


def sifat_sahifasi():
    guruhlar, _, cv = yukla()
    st.title('📊 Model sifati')
    st.markdown(
        "Model — XGBoost, bozordagi nomzodlarning o'tish balidan yuqori ball olgan **ulushi**ni bashorat qiladi, "
        "keyin bu ulush bozordagi ballar taqsimoti orqali ballga qaytariladi. Grant va shartnoma — alohida.\n\n"
        "- **GroupKFold (OTM)** — model sinov OTM larini umuman ko'rmagan (qattiq sinov).\n"
        "- **KFold (tasodifiy)** — OTM lar ma'lum, yo'nalishlar yangi. Ilovadagi bashoratlar shu usuldan."
    )

    tur = st.radio("O'rin turi", ['grant', 'shartnoma'], horizontal=True,
                   format_func={'grant': 'Grant', 'shartnoma': 'Shartnoma'}.get)
    j = cv[cv['tur'] == tur].drop(columns='tur')
    st.dataframe(j, hide_index=True, width='stretch',
                 column_config={'bolish': 'Tekshirish usuli', 'model': 'Model',
                                '<=5 ball': st.column_config.NumberColumn('≤5 ball', format='percent'),
                                '<=10 ball': st.column_config.NumberColumn('≤10 ball', format='percent')})
    st.caption("`median` — bozor × yo'nalish bo'yicha median (baseline); `chegara` — o'rinlar eng yaxshi "
               "nomzodlardan to'ldirilsa, oxirgi o'rindagi ball; `xgb_ball` / `xgb_ulush` — XGBoost modellari. "
               "MAE va RMSE — ballarda.")

    d = guruhlar[guruhlar[f'{tur}_bali'].notna()]
    st.subheader('Bashorat va haqiqiy ball')
    st.scatter_chart(d.rename(columns={f'{tur}_bali': '2026 haqiqiy', f'{tur}_bashorat': 'Bashorat'}),
                     x='2026 haqiqiy', y='Bashorat', size=8)

    st.subheader('Bozorlar bo\'yicha xato')
    xato = (d[f'{tur}_bashorat'] - d[f'{tur}_bali']).abs()
    jadval = (pd.DataFrame({'bozor': d['bozor'], 'xato': xato, 'ball': d[f'{tur}_bali']})
                .groupby('bozor').agg(guruhlar=('xato', 'size'), MAE=('xato', 'mean'),
                                      ortacha_ball=('ball', 'mean'))
                .sort_values('guruhlar', ascending=False).round(1).reset_index())
    st.dataframe(jadval, hide_index=True, width='stretch',
                 column_config={'bozor': 'Bozor', 'guruhlar': 'Guruhlar', 'MAE': 'MAE (ball)',
                                'ortacha_ball': "O'rtacha o'tish bali"})
    st.caption("Bozor — nomzodlari umumiy bo'lgan fanlar juftliklari guruhi. Kichik bozorlarda (10 dan kam "
               "guruh) ilova umumiy o'rtacha xatoni ishlatadi.")


sahifa = st.navigation([
    st.Page(abituriyent_sahifasi, title='Abituriyent uchun', icon='🎓', url_path='abituriyent', default=True),
    st.Page(yunalish_sahifasi, title="Yo'nalish bo'yicha", icon='📍', url_path='yunalish'),
    st.Page(sifat_sahifasi, title='Model sifati', icon='📊', url_path='sifat'),
])
sahifa.run()
