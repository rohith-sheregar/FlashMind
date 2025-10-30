"""
Fine-tune google/flan-t5-base on educational Q&A pairs in JSONL format.

Usage:
  # From VS Code or terminal:
  python ml_service/scripts/train_model.py \
    --data ml_service/data/processed/train.jsonl \
    --out ml_service/models/flashmind_v1/

Requirements:
- Hugging Face transformers, datasets, torch
- GPU recommended (uses CUDA if available)

Arguments:
  --data: Path to JSONL training data (default: ml_service/data/processed/train.jsonl)
  --out:  Output directory for model/tokenizer (default: ml_service/models/flashmind_v1/)

Each line in the JSONL must have:
{"input": "...", "output": "..."}
"""

import os
import argparse
from pathlib import Path
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    Trainer,
    TrainingArguments,
    DataCollatorForSeq2Seq,
)

def main():
    parser = argparse.ArgumentParser(
        description="Fine-tune a T5 model for Q&A generation."
    )
    parser.add_argument(
        "--data",
        type=str,
        default="ml_service/data/processed/train.jsonl",
        help="Path to JSONL training data",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="ml_service/models/flashmind_v1/",
        help="Output directory for model/tokenizer",
    )
    parser.add_argument(
        "--model_name", type=str, default="google/flan-t5-base", help="Base model to fine-tune."
    )
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=4, help="Training batch size per device.")
    parser.add_argument(
        "--lr", type=float, default=5e-5, help="Learning rate."
    )
    parser.add_argument(
        "--test_size", type=float, default=0.1, help="Proportion of data for validation."
    )
    args = parser.parse_args()

    output_dir = args.out
    model_name = args.model_name
    max_input_length = 256
    max_output_length = 256
    logging_steps = 50

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Load dataset
    if not Path(args.data).exists():
        raise FileNotFoundError(f"Training data not found at {args.data}")
    dataset = load_dataset("json", data_files=args.data, split="train")
    dataset = dataset.train_test_split(test_size=args.test_size, seed=42)
    train_ds = dataset["train"]
    val_ds = dataset["test"]

    # Load tokenizer/model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    model = model.to(device)

    def preprocess(batch):
        # Tokenize input and output with truncation and padding
        model_inputs = tokenizer(
            batch["input"],
            max_length=max_input_length,
            truncation=True,
            padding="max_length",
        )
        labels = tokenizer(
            batch["output"],
            max_length=max_output_length,
            truncation=True,
            padding="max_length",
        )
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    train_ds = train_ds.map(preprocess, batched=True, remove_columns=train_ds.column_names)
    val_ds = val_ds.map(preprocess, batched=True, remove_columns=val_ds.column_names)

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    training_args = TrainingArguments(
        output_dir=output_dir,
        evaluation_strategy="epoch",
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        save_total_limit=2,
        fp16=torch.cuda.is_available(),
        logging_steps=logging_steps,
        save_strategy="epoch",
        report_to="none",
        remove_unused_columns=True,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    print("Starting training...")
    trainer.train()

    print("Evaluating on validation set...")
    metrics = trainer.evaluate()
    print(f"Validation loss: {metrics.get('eval_loss', None):.4f}")

    # Save model and tokenizer
    print(f"Saving model and tokenizer to {output_dir}")
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    # Sample generations
    print("\nSample generations:")
    val_raw = load_dataset("json", data_files=args.data, split="train").train_test_split(test_size=args.test_size, seed=42)["test"]
    for i in range(min(5, len(val_raw))):
        prompt = val_raw[i]["input"]
        gt = val_raw[i]["output"]
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding="max_length", max_length=max_input_length).to(device)
        with torch.no_grad():
            gen_ids = model.generate(
                **inputs,
                max_length=max_output_length,
                num_beams=2,
            )
        gen_text = tokenizer.decode(gen_ids[0], skip_special_tokens=True)
        print(f"\nInput: {prompt}\nTarget: {gt}\nGenerated: {gen_text}")

if __name__ == "__main__":
    main()
