"""Compare a human reference transcript with a VoiceIQ hypothesis transcript."""
import argparse
from pathlib import Path

from app_core.metrics import word_error_rate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="Path to the manually verified reference .txt")
    parser.add_argument("hypothesis", type=Path, help="Path to the VoiceIQ transcript .txt")
    args = parser.parse_args()

    reference = args.reference.read_text(encoding="utf-8-sig")
    hypothesis = args.hypothesis.read_text(encoding="utf-8-sig")
    score = word_error_rate(reference, hypothesis)
    print(f"WER: {score:.4f} ({score * 100:.2f}%)")
    print(f"Reference words: {len(reference.split())}")
    print(f"Hypothesis words: {len(hypothesis.split())}")


if __name__ == "__main__":
    main()
