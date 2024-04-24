import random
import argparse
from pathlib import Path
import pandas as pd
from datasets import Dataset

def parse_args():
    parser = argparse.ArgumentParser("Data Downloader")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="JSONlines file with urls and hashes",
        required=True,
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="output directory", required=True
    )
    
    parser.add_argument(
        "-k", "--kfold", type=int, required=True
    )
    parser.add_argument(
        "--huggingface", type=int, required=True
    )
    return parser.parse_args()

def main():
    # Split the data in k pieces and save it locally
    args = parse_args()

    with open(args.input) as f:
        data = f.readlines()

    for _ in range(10):
        random.shuffle(data)
    split_size = len(data) // args.kfold
    parts = [data[i:i + split_size] for i in range(0, len(data), split_size)]
    
    if len(parts[-1]) < split_size:
        parts[-2].extend(parts[-1])
        parts.pop()

    for i, part in enumerate(parts):
        if args.huggingface:
            Dataset.from_pandas(pd.DataFrame(part))\
                   .push_to_hub('jstonge1/fpNER', split=f"part_{i}")
        
        #!TODO: TO CHECK
        with open(args.output / f"part_{i}.txt", "w") as f:
            f.writelines(part)