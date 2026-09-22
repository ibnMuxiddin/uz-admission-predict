"""
Yelp sharhlarini TypeSafe AI Jev modeli yordamida klassifikatsiya qilish skripti.

Ushbu skript yelp_reviews.csv faylidagi "text" ustunini o'qiydi va har bir sharhni
Jev modeli (TypeSafe System One API) orqali:
  - ijobiy (positive)
  - salbiy (negative)
  - neytral (neutral)
toifalariga ajratadi.

API kalit .env faylidagi TYPESAFE_API_KEY o'zgaruvchisidan olinadi.
Hujjat: https://docs.typesafe.ai/llms.txt
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
from typesafe_sdk import AsyncTypeSafeClient, Choice, RetryPolicy, TypeSafeClient

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("classify_reviews")

# HTTP so'rovlarining har birini alohida log qilmaslik (progress bar toza ko'rinishi uchun)
for _log_name in ["httpx", "httpx2", "httpcore", "httpcore2", "typesafe_sdk"]:
    logging.getLogger(_log_name).setLevel(logging.WARNING)


# Jev modeli uchun Choice savoli konfiguratsiyasi
SENTIMENT_QUESTION = Choice(
    instructions=(
        "Mijozning ushbu sharhini ijobiy, salbiy yoki neytral toifalardan biriga ajrating "
        "(Classify the customer review into positive, negative, or neutral sentiment)."
    ),
    criteria={
        "ijobiy": "Positive review: mijoz xizmat, taom yoki mahsulotdan mamnun, ijobiy taassurot yoki maqtov bildirgan.",
        "salbiy": "Negative review: mijoz norozi, tanqid, e'tiroz, shikoyat yoki yomon tajriba bildirgan.",
        "neytral": "Neutral review: xolis bayon, aralash fikr yoki na aniq ijobiy va na aniq salbiy his-tuyg'u mavjud bo'lmagan sharh.",
    },
)


def get_api_key() -> str:
    """
    .env faylidan TYPESAFE_API_KEY ni o'qiydi va tekshiradi.
    """
    # .env faylini joriy papkadan yoki ota papkalardan yuklash
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()

    api_key = os.getenv("TYPESAFE_API_KEY")
    if not api_key:
        logger.error(
            "\n" + "=" * 60 + "\n"
            "XATOLIK: .env faylida 'TYPESAFE_API_KEY' topilmadi!\n"
            "Iltimos, loyiha ildizidagi .env fayliga API kalitingizni kiriting:\n\n"
            "  TYPESAFE_API_KEY=your_actual_api_key_here\n\n"
            "API kalitni olish uchun: https://console.typesafe.ai/keys\n"
            + "=" * 60
        )
        sys.exit(1)
    return api_key


async def classify_single_review(
    client: AsyncTypeSafeClient,
    text: str,
    model: str,
    semaphore: asyncio.Semaphore,
) -> Dict[str, Any]:
    """
    Bitta sharh matnini Jev modeli orqali klassifikatsiya qiladi.
    """
    # Matn bo'sh yoki NaN bo'lsa
    if not isinstance(text, str) or not text.strip():
        return {
            "sentiment": "neytral",
            "sentiment_confidence": 0.0,
            "prob_ijobiy": 0.0,
            "prob_salbiy": 0.0,
            "prob_neytral": 1.0,
        }

    # API ga so'rov yuborish
    async with semaphore:
        try:
            response = await client.system_one(
                state=text,
                model=model,
                questions={"sentiment": SENTIMENT_QUESTION},
            )
            answer = response.answers["sentiment"]
            probs = getattr(answer, "probabilities", {}) or {}

            return {
                "sentiment": answer.choice,
                "sentiment_confidence": round(float(answer.confidence), 4),
                "prob_ijobiy": round(float(probs.get("ijobiy", 0.0)), 4),
                "prob_salbiy": round(float(probs.get("salbiy", 0.0)), 4),
                "prob_neytral": round(float(probs.get("neytral", 0.0)), 4),
            }
        except Exception as e:
            logger.warning("Sharhni baholashda xatolik yuz berdi: %s", e)
            return {
                "sentiment": "xatolik",
                "sentiment_confidence": 0.0,
                "prob_ijobiy": 0.0,
                "prob_salbiy": 0.0,
                "prob_neytral": 0.0,
            }


async def process_reviews_async(
    df: pd.DataFrame,
    api_key: str,
    model: str,
    concurrency: int,
    output_path: Path,
    checkpoint_interval: int = 50,
) -> pd.DataFrame:
    """
    Sharhlarni asinxron tarzda baholaydi va vaqti-vaqti bilan faylga saqlab boradi.
    """
    semaphore = asyncio.Semaphore(concurrency)
    retry_policy = RetryPolicy(max_retries=5, backoff_initial=1.0, backoff_max=10.0)

    async with AsyncTypeSafeClient(api_key=api_key, retry=retry_policy) as client:

        pbar = tqdm(total=len(df), desc="Sharhlar klassifikatsiya qilinmoqda", unit="ta")

        # Natijalarni saqlash
        sentiments: List[Optional[str]] = list(df.get("sentiment", [None] * len(df)))
        confidences: List[Optional[float]] = list(
            df.get("sentiment_confidence", [None] * len(df))
        )
        prob_i: List[Optional[float]] = list(df.get("prob_ijobiy", [None] * len(df)))
        prob_s: List[Optional[float]] = list(df.get("prob_salbiy", [None] * len(df)))
        prob_n: List[Optional[float]] = list(df.get("prob_neytral", [None] * len(df)))

        # Oldindan hisoblangan qatorlarni aniqlash
        pending_indices = [
            i for i, s in enumerate(sentiments) if pd.isna(s) or s is None or s == ""
        ]
        already_done = len(df) - len(pending_indices)
        if already_done > 0:
            logger.info("%d ta sharh oldindan tayyor, o'tkazib yuborilmoqda.", already_done)
            pbar.update(already_done)

        async def worker(idx: int, review_text: str):
            res = await classify_single_review(client, review_text, model, semaphore)
            sentiments[idx] = res["sentiment"]
            confidences[idx] = res["sentiment_confidence"]
            prob_i[idx] = res["prob_ijobiy"]
            prob_s[idx] = res["prob_salbiy"]
            prob_n[idx] = res["prob_neytral"]
            pbar.update(1)

        # Batchlar bo'yicha rejalashtirish
        chunk_size = checkpoint_interval
        for i in range(0, len(pending_indices), chunk_size):
            chunk_indices = pending_indices[i : i + chunk_size]
            tasks = [worker(idx, str(df.at[idx, "text"])) for idx in chunk_indices]
            await asyncio.gather(*tasks)

            # Oraliq natijalarni saqlab borish (checkpoint)
            df["sentiment"] = sentiments
            df["sentiment_confidence"] = confidences
            df["prob_ijobiy"] = prob_i
            df["prob_salbiy"] = prob_s
            df["prob_neytral"] = prob_n

            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False, encoding="utf-8")

        pbar.close()

    return df


def main():
    parser = argparse.ArgumentParser(
        description="Yelp sharhlarini TypeSafe Jev modeli orqali ijobiy / salbiy / neytral toifalarga klassifikatsiya qilish."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/processed/yelp_reviews.csv",
        help="Kiruvchi CSV fayl yo'li (standart: data/processed/yelp_reviews.csv)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/processed/yelp_reviews_classified.csv",
        help="Chiquvchi CSV fayl yo'li (standart: data/processed/yelp_reviews_classified.csv)",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        help="Klassifikatsiya qilinadigan sharhlar sonini cheklash (masalan sinov uchun: 10)",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="jev-latest",
        help="TypeSafe Jev modeli nomi (standart: jev-latest)",
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=5,
        help="Bir vaqtda yuboriladigan parallel so'rovlar soni (standart: 5)",
    )
    parser.add_argument(
        "--checkpoint-interval",
        type=int,
        default=50,
        help="Oraliq saqlash oraliq soni (standart: har 50 ta sharhda)",
    )
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        default=None,
        help="Bitta alohida sharh matnini darhol tekshirish uchun (sinov maqsadida).",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Agar chiquvchi fayl mavjud bo'lsa, davom ettirmasdan qaytadan boshlash.",
    )

    args = parser.parse_args()

    # 1. API kalitni tekshirish
    api_key = get_api_key()

    # 1.1. Agar faqat bitta matn berilgan bo'lsa
    if args.text:
        logger.info("Bitta sharh tekshirilmoqda: %s", args.text)
        with TypeSafeClient(api_key=api_key) as client:
            resp = client.system_one(
                state=args.text,
                model=args.model,
                questions={"sentiment": SENTIMENT_QUESTION},
            )
            ans = resp.answers["sentiment"]
            probs = getattr(ans, "probabilities", {}) or {}
            print("\n" + "=" * 40)
            print(f"Sharh matni: {args.text}")
            print(f"Natija (Sentiment): {ans.choice.upper()}")
            print(f"Ishonch darajasi (Confidence): {ans.confidence:.2%}")
            print("Ehtimolliklar (Probabilities):")
            for k, v in probs.items():
                print(f"  - {k}: {v:.2%}")
            print("=" * 40 + "\n")
        return

    # 2. Kiruvchi faylni tekshirish

    input_file = Path(args.input)
    if not input_file.exists():
        logger.error("Kiruvchi CSV fayl topilmadi: %s", input_file)
        sys.exit(1)

    output_file = Path(args.output)

    logger.info("Kiruvchi fayl yuklanmoqda: %s", input_file)
    df = pd.read_csv(input_file)

    if "text" not in df.columns:
        logger.error("CSV faylida 'text' ustuni topilmadi! Mavjud ustunlar: %s", list(df.columns))
        sys.exit(1)

    logger.info("Jami sharhlar soni: %d", len(df))

    # Cheklash bo'lsa
    if args.limit and args.limit > 0:
        df = df.iloc[: args.limit].copy()
        logger.info("Cheklov o'rnatildi: dastlabki %d ta sharh olinmoqda.", len(df))

    # Resume (davom ettirish) tekshiruvi
    if not args.no_resume and output_file.exists():
        try:
            prev_df = pd.read_csv(output_file)
            if "sentiment" in prev_df.columns:
                # review_id bo'yicha yoki index bo'yicha moslash
                if "review_id" in df.columns and "review_id" in prev_df.columns:
                    prev_map = prev_df.set_index("review_id")[
                        ["sentiment", "sentiment_confidence", "prob_ijobiy", "prob_salbiy", "prob_neytral"]
                    ].to_dict(orient="index")

                    for idx, row in df.iterrows():
                        r_id = row.get("review_id")
                        if r_id in prev_map and pd.notna(prev_map[r_id]["sentiment"]):
                            for col in ["sentiment", "sentiment_confidence", "prob_ijobiy", "prob_salbiy", "prob_neytral"]:
                                df.at[idx, col] = prev_map[r_id][col]
                else:
                    for col in ["sentiment", "sentiment_confidence", "prob_ijobiy", "prob_salbiy", "prob_neytral"]:
                        if col in prev_df.columns:
                            df[col] = prev_df[col]
                logger.info("Mavjud %s faylidan oraliq natijalar yuklandi.", output_file)
        except Exception as e:
            logger.warning("Mavjud natijalarni o'qishda xatolik bo'ldi, qaytadan boshlanadi: %s", e)

    # 3. Asinxron klassifikatsiya jarayoni
    logger.info("Model: %s | Concurrency: %d", args.model, args.concurrency)
    result_df = asyncio.run(
        process_reviews_async(
            df=df,
            api_key=api_key,
            model=args.model,
            concurrency=args.concurrency,
            output_path=output_file,
            checkpoint_interval=args.checkpoint_interval,
        )
    )

    # 4. Natijalarni yakuniy saqlash
    output_file.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_file, index=False, encoding="utf-8")
    logger.info("Klassifikatsiya muvaffaqiyatli yakunlandi! Natija saqlandi: %s", output_file)

    # Statistika xulosasi
    if "sentiment" in result_df.columns:
        logger.info("\n--- Klassifikatsiya natijalari taqsimoti ---")
        summary = result_df["sentiment"].value_counts().to_string()
        print(summary)


if __name__ == "__main__":
    main()
