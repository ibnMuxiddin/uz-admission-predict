"""
classify_reviews.py uchun mock test.
TypeSafe API chaqiruvini simulyatsiya qilib to'liq pipeline ishlashini tekshiradi.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from classify_reviews import process_reviews_async, SENTIMENT_QUESTION



class FakeChoiceAnswer:
    def __init__(self, choice, confidence, probabilities):
        self.choice = choice
        self.confidence = confidence
        self.probabilities = probabilities


class FakeResponse:
    def __init__(self, choice, confidence, probabilities):
        self.answers = {
            "sentiment": FakeChoiceAnswer(choice, confidence, probabilities)
        }


async def test_mock_classification():
    # Sinov dataframe
    test_data = {
        "review_id": ["rev_1", "rev_2", "rev_3"],
        "text": [
            "Great food and amazing service! Loved the pizza.",
            "Horrible experience, rude staff and cold food.",
            "The place is located downtown next to the library.",
        ],
    }
    df = pd.DataFrame(test_data)
    output_path = Path("scratch/test_output.csv")

    mock_answers = [
        FakeResponse("ijobiy", 0.98, {"ijobiy": 0.98, "salbiy": 0.01, "neytral": 0.01}),
        FakeResponse("salbiy", 0.95, {"ijobiy": 0.02, "salbiy": 0.95, "neytral": 0.03}),
        FakeResponse("neytral", 0.89, {"ijobiy": 0.05, "salbiy": 0.06, "neytral": 0.89}),
    ]

    call_count = 0

    async def fake_system_one(*args, **kwargs):
        nonlocal call_count
        ans = mock_answers[call_count % len(mock_answers)]
        call_count += 1
        return ans

    with patch("classify_reviews.AsyncTypeSafeClient") as MockClientClass:
        mock_instance = AsyncMock()
        mock_instance.system_one.side_effect = fake_system_one
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        MockClientClass.return_value = mock_instance

        res_df = await process_reviews_async(
            df=df,
            api_key="fake-test-key",
            model="jev-latest",
            concurrency=2,
            output_path=output_path,
            checkpoint_interval=2,
        )

        print("\nTest natijalari:")
        print(res_df[["review_id", "sentiment", "sentiment_confidence", "prob_ijobiy", "prob_salbiy", "prob_neytral"]])

        assert res_df.at[0, "sentiment"] == "ijobiy"
        assert res_df.at[1, "sentiment"] == "salbiy"
        assert res_df.at[2, "sentiment"] == "neytral"
        assert output_path.exists()
        print("\nBARCHA TESTLAR MUVAFFAQIYATLI O'TDI!")


if __name__ == "__main__":
    asyncio.run(test_mock_classification())
