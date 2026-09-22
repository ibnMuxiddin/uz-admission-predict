# 🎓 OTM o'tish ballari bashorati · University Cut-off Score Prediction

**[O'zbekcha](#-ozbekcha)** · **[English](#-english)**

O'zbekiston oliy ta'lim muassasalariga (OTM) kirish uchun o'tish ballarini bashorat qilish:
mandat.uzbmb.uz ma'lumotlari, ma'lumotlar tahlili, XGBoost modeli va Streamlit ilovasi.

Predicting admission cut-off scores for Uzbek universities: mandat.uzbmb.uz data, data analysis,
an XGBoost model and a Streamlit app.

---

## 🇺🇿 O'zbekcha

### Loyiha haqida

2026 yildan qabul tartibi o'zgardi. Endi abituriyent **avval imtihon topshiradi**, balini biladi va
**shundan keyin** yo'nalish tanlaydi. 56.7 va undan yuqori ball olganlar tanlovda qatnasha oladi.

Loyiha shu savolga javob beradi: *"Mening balim va fanlarim bilan qaysi yo'nalishlarga kira olaman?"*
Buning uchun har bir guruhning (OTM × yo'nalish × ta'lim tili × ta'lim shakli) grant va to'lov-shartnoma
bo'yicha o'tish bali bashorat qilinadi.

| Ko'rsatkich | Qiymat |
|---|---|
| Abituriyentlar (tanlov ishtirokchilari) | 357 561 |
| Abituriyent tanlovlari | 1 787 836 |
| Guruhlar (OTM × yo'nalish × til × shakl) | 5 547 |
| OTM lar | 105 |
| Raqobat bozorlari | 32 |

### Asosiy g'oyalar

**1. Faqat 2026 yil.** Oldingi yillarda avval yo'nalish tanlanib, keyin imtihon topshirilgan. Tanlov
mexanizmi boshqacha bo'lgani uchun eski yillar solishtirib bo'lmaydi. Abituriyentlar haqidagi batafsil
ma'lumot ham faqat 2026 yilda e'lon qilingan.

**2. Data leakage'dan himoya.** Abituriyentlarning qaysi OTM va yo'nalishni tanlagani mandatdan keyin
e'lon qilinadi. Bashorat paytida bu ma'lumot bo'lmaydi, shuning uchun belgi sifatida ishlatilmaydi.
Nomzodlarning **ballari va imtihon fanlari** esa tanlovdan oldin ma'lum, ular belgi bo'la oladi.

**3. Raqobat bozori.** Abituriyentning bali hamma tanlovlarida bir xil va u bir nechta fanlar juftligiga
hujjat topshira oladi. Masalan, bitta nomzod `Matematika + Fizika` va `Fizika + Matematika` yo'nalishlariga
birga hujjat topshirgan. Nomzodlari umumiy bo'lgan fanlar juftliklari bitta **bozorga** birlashtirildi:
38 ta juftlikdan 32 ta bozor chiqdi.

**4. Nisbiy maqsad.** Model o'tish balining o'zini emas, **bozordagi nomzodlarning qancha qismi o'tish
balidan yuqori ball olganini** (ulush) bashorat qiladi. Keyingi yil nomzodlar soni va ballar taqsimoti
o'zgaradi, ulush esa yangi taqsimotga qo'yilib ballga qaytariladi.

### Ma'lumotlar oqimi

```
mandat.uzbmb.uz
├── abiturents.csv   (har bir abituriyentning har bir tanlovi)
│     └── 01 → 03 → 04 ─────────────────────────┐
└── otm_2026.csv     (kvotalar va o'tish ballari) │
      └── 05 → 06 (fanlar, raqobat bozorlari) ────┤
                                                  ▼
                          07 Feature Engineering → model_data.csv
                                                  ▼
                          08 Modellashtirish → XGBoost modellari
                                                  ▼
                          Streamlit ilovasi (app/)
```

| Notebook | Bosqich | Nima qiladi |
|---|---|---|
| `01` | Skreyping | Abituriyentlar ro'yxati, fanlarni biriktirish |
| `02` | Skreyping | Mandat saytini sinash (qoralama) |
| `03` | Data Understanding | Abituriyentlar: ballar taqsimoti, fanlar, sifat |
| `04` | Data Preparation | Fan nomlarini bir xillashtirish, fanlar juftligi |
| `05` | Data Understanding | OTM lar: kvotalar, o'tish ballari, takrorlar |
| `06` | Data Preparation | Tozalash, fanlarni biriktirish, raqobat bozorlari |
| `07` | Feature Engineering | Bozor darajasidagi raqobat belgilari, nisbiy maqsad |
| `08` | Modellashtirish | Baseline va XGBoost, kross-validatsiya |

### Natijalar

MAE — o'rtacha xato, ballarda (qancha past bo'lsa, shuncha yaxshi).

| Model | Grant, GroupKFold | Grant, KFold | Shartnoma, GroupKFold | Shartnoma, KFold |
|---|---|---|---|---|
| Median (baseline) | 9.61 | 9.31 | 16.33 | 15.80 |
| Bozorning taxminiy chegarasi | 23.35 | 23.35 | 20.28 | 20.28 |
| XGBoost, xom ball | 9.84 | 8.58 | **13.11** | 12.73 |
| XGBoost, nisbiy ulush | **9.38** | **8.13** | 13.11 | **12.56** |

- **GroupKFold (OTM)** — model sinovdagi OTM larni umuman ko'rmagan (qattiq sinov).
- **KFold (tasodifiy)** — OTM lar ma'lum, yo'nalishlar yangi. Keyingi yilga yaqinroq holat.
- Shartnoma bo'yicha XGBoost baseline dan ~20% aniqroq. Grant bo'yicha ustunlik kichik: bozor va yo'nalish
  bo'yicha median o'zi juda kuchli.
- Eng muhim belgilar bozor darajasida: ballar kvantillari, bitta o'ringa nechta nomzod, taxminiy chegara.

### Streamlit ilovasi

Uchta sahifa:

- **🎓 Abituriyent uchun.** Fanlar va ballni kiritasiz, yo'nalishlar ro'yxati chiqadi: bashorat, balingiz
  bilan farq va holat (🟢 yuqori · 🟡 chegarada · 🔴 past).
- **📍 Yo'nalish bo'yicha.** OTM, yo'nalish, til va shaklni tanlaysiz: bashorat, 2026 yilgi haqiqiy ball
  va o'rtacha xato.
- **📊 Model sifati.** Kross-validatsiya natijalari va bozorlar bo'yicha xatolar.

Ilova modellarni ishga tushirmaydi. Bashoratlar oldindan hisoblanib, `app/data/` ga yozilgan (~1.2 MB).
Har bir bashorat shu yo'nalishni o'qitishda ko'rmagan modeldan olingan (kross-validatsiya).

### Ishga tushirish

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Faqat ilova
pip install -r app/requirements.txt
streamlit run app/streamlit_app.py
```

To'liq jarayon: skreyperlar (`src/data/`) → `notebooks/` dagi notebooklar tartib bilan (`notebooks/`
papkasidan ishga tushiriladi) → `python src/deploy/build_artifacts.py` → ilova.

`data/` va `models/` papkalari repoda yo'q: ular hajmi katta va skreyperlar hamda notebooklar orqali
qayta yaratiladi.

### Cheklovlar

- Model bitta yil (2026) ma'lumotida o'qitilgan. Raqobat o'zgarganda qanday ishlashini faqat keyingi yil
  ma'lumotlari bilan tekshirish mumkin.
- Ba'zi bozorlarda xato katta, masalan shartnoma bo'yicha `Tarix + Chet tili` va
  `Tarix + Ona tili va adabiyoti` bozorlarida o'rtacha 30 ball atrofida.
- Ilovadagi holat belgisi ehtimollik emas, taxminiy yo'l-yo'riq. Yakuniy qaror uchun rasmiy manbaga
  (mandat.uzbmb.uz) tayaning.

---

## 🇬🇧 English

### About

Uzbekistan changed its admission rules in 2026. Applicants now **sit the exam first**, learn their score,
and **only then** choose programs. Everyone scoring 56.7 or higher can take part in the selection.

The project answers one question: *"With my score and exam subjects, which programs can I get into?"*
To do that, it predicts the grant (state-funded) and contract (paid) cut-off score for every group
(university × program × language × study form).

| Metric | Value |
|---|---|
| Applicants (selection participants) | 357,561 |
| Applicant choices | 1,787,836 |
| Groups (university × program × language × form) | 5,547 |
| Universities | 105 |
| Competition markets | 32 |

### Key ideas

**1. 2026 only.** In earlier years applicants chose programs before the exam. The selection mechanism was
different, so earlier years are not comparable. Detailed applicant data was also published only in 2026.

**2. No data leakage.** Which university and program each applicant chose is published after the admission
results, so it is never used as a feature. Applicants' **scores and exam subjects** are known before the
selection and are valid features.

**3. Competition markets.** An applicant has one score for all choices and may apply to several subject
pairs. For example, the same applicants apply to both `Matematika + Fizika` and `Fizika + Matematika`
programs. Subject pairs that share applicants are merged into one **market**: 38 pairs form 32 markets.

**4. Relative target.** Instead of the raw cut-off score, the model predicts **the share of the market's
applicants who scored at or above the cut-off**. Next year the number of applicants and the score
distribution will change; the predicted share is mapped back to a score on the new distribution.

### Pipeline

| Notebook | Stage | What it does |
|---|---|---|
| `01` | Scraping | Applicant lists, attach exam subjects |
| `02` | Scraping | Probe of the mandate site (draft) |
| `03` | Data Understanding | Applicants: score distribution, subjects, quality |
| `04` | Data Preparation | Normalize subject names, build subject pairs |
| `05` | Data Understanding | Programs: quotas, cut-off scores, duplicates |
| `06` | Data Preparation | Cleaning, subject lookup, competition markets |
| `07` | Feature Engineering | Market-level competition features, relative target |
| `08` | Modeling | Baselines and XGBoost, cross-validation |

### Results

MAE is the mean absolute error in score points (lower is better).

| Model | Grant, GroupKFold | Grant, KFold | Contract, GroupKFold | Contract, KFold |
|---|---|---|---|---|
| Median (baseline) | 9.61 | 9.31 | 16.33 | 15.80 |
| Market cut-off rule | 23.35 | 23.35 | 20.28 | 20.28 |
| XGBoost, raw score | 9.84 | 8.58 | **13.11** | 12.73 |
| XGBoost, relative share | **9.38** | **8.13** | 13.11 | **12.56** |

- **GroupKFold (by university)**: the model never saw the test universities (strict test).
- **KFold (random)**: universities are known, programs are new. This is closer to the next-year use case.
- For contract seats XGBoost beats the baseline by ~20%. For grant seats the gain is small: the
  market × program median is already a strong predictor.
- The most important features are market-level: score quantiles, applicants per seat, the market cut-off.

### Streamlit app

Three pages:

- **🎓 For applicants.** Enter your subjects and score to get a list of programs with the predicted
  cut-off, your margin, and a status (🟢 above · 🟡 borderline · 🔴 below).
- **📍 By program.** Pick a university, program, language and form to see the prediction, the actual
  2026 cut-off and the typical error.
- **📊 Model quality.** Cross-validation results and error by market.

The app does not run the models. Predictions are precomputed into `app/data/` (~1.2 MB). Every prediction
comes from a model that did not see that program during training (cross-validation).

### Getting started

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# App only
pip install -r app/requirements.txt
streamlit run app/streamlit_app.py
```

Full pipeline: scrapers (`src/data/`) → notebooks in order (run from `notebooks/`) →
`python src/deploy/build_artifacts.py` → app.

The `data/` and `models/` folders are not in the repo: they are large and are regenerated by the
scrapers and notebooks.

### Limitations

- The model is trained on a single year (2026). How it handles changing competition can only be checked
  with next year's data.
- Errors are large in some markets, e.g. around 30 points for contract seats in `Tarix + Chet tili` and
  `Tarix + Ona tili va adabiyoti`.
- The status label in the app is a rough guide, not a probability. Rely on the official source
  (mandat.uzbmb.uz) for final decisions.

---

### Loyiha tuzilishi · Project structure

```
app/                  Streamlit ilovasi · Streamlit app
  data/               Oldindan hisoblangan bashoratlar · precomputed predictions
notebooks/            01–08 tahlil va modellashtirish · analysis and modeling
references/           Qo'lda tuzilgan manbalar · hand-made references
reports/              Kross-validatsiya natijalari · CV results
src/data/             Skreyperlar · scrapers
src/deploy/           Ilova uchun ma'lumot tayyorlash · app artifact builder
```
