"""
Evaluate fine-tuned flashcard model quality using ROUGE and BLEU.

- Loads model from ml_service/models/flashmind_v1/
- Evaluates on a validation JSONL file (with 'input' and 'output' fields)
- Computes ROUGE-L and BLEU scores between generated and gold answers
- Prints top 3 best and worst examples by ROUGE-L

Usage:
    python ml_service/scripts/evaluate_model.py --val ml_service/data/processed/val.jsonl
"""
import argparse
import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from datasets import load_metric
from tqdm import tqdm

MODEL_PATH = "ml_service/models/flashmind_v1/"


def load_validation_data(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            data.append(obj)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--val", type=str, required=True, help="Validation JSONL file")
    args = parser.parse_args()

    val_data = load_validation_data(args.val)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_PATH)
    model.eval()

    rouge = load_metric("rouge")
    bleu = load_metric("bleu")

    results = []
    for ex in tqdm(val_data, desc="Evaluating"):
        prompt = ex["input"]
        gold = ex["output"]
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding="max_length", max_length=256)
        with torch.no_grad():
            gen_ids = model.generate(**inputs, max_length=256, num_beams=2)
        pred = tokenizer.decode(gen_ids[0], skip_special_tokens=True)
        # Compute metrics
        rouge_out = rouge.compute(predictions=[pred], references=[gold], rouge_types=["rougeL"])
        bleu_out = bleu.compute(predictions=[[pred.split()]], references=[[gold.split()]])
        results.append({
            "input": prompt,
            "gold": gold,
            "pred": pred,
            "rougeL": rouge_out["rougeL"].fmeasure,
            "bleu": bleu_out["bleu"]
        })

    # Sort by ROUGE-L
    results_sorted = sorted(results, key=lambda x: x["rougeL"], reverse=True)
    print("\nTop 3 Best Examples (by ROUGE-L):")
    for r in results_sorted[:3]:
        print(f"\nInput: {r['input']}\nGold: {r['gold']}\nPred: {r['pred']}\nROUGE-L: {r['rougeL']:.3f}  BLEU: {r['bleu']:.3f}")
    print("\nTop 3 Worst Examples (by ROUGE-L):")
    for r in results_sorted[-3:]:
        print(f"\nInput: {r['input']}\nGold: {r['gold']}\nPred: {r['pred']}\nROUGE-L: {r['rougeL']:.3f}  BLEU: {r['bleu']:.3f}")

    # Print overall scores
    avg_rouge = sum(r["rougeL"] for r in results) / len(results)
    avg_bleu = sum(r["bleu"] for r in results) / len(results)
    print(f"\nAverage ROUGE-L: {avg_rouge:.3f}")
    print(f"Average BLEU: {avg_bleu:.3f}")

if __name__ == "__main__":
    import torch
    main()
