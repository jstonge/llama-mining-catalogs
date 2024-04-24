import argparse
from pathlib import Path
import Image
import io

import json

import kitty
import numpy as np

from helpers import (
    get_annotations, 
    post_LS, 
    get_pngid_to_annotate_balanced
)

def parse_args():
    parser = argparse.ArgumentParser("Data Downloader")
    parser.add_argument("--ror", required=True)
    return parser.parse_args()


def main() -> None:
    """
    BBA -> full-page NER

    For now, we simply push all the data from BBA to fpNER (REA).
    Then we balance fpNER project using another function.
    """
    args = parse_args()
    
    fpNER_PROJ_ID = 59149 # full-page NER project (REA)
    BBA_PROJ_ID = 58960 # BBA project
    RORs = ['05x2bcf33', '0155zta11', '046rm7j60']

    cat_db = kitty.CatalogDB()
    ror_id = args.ror

    bba_annots = get_annotations(BBA_PROJ_ID, type='JSON', only_annots=True)
    fpNER_annots = get_annotations(fpNER_PROJ_ID, type='JSON', only_annots=False)

    if ror_id is not None:
        ror_bba = [_ for _ in bba_annots if Path(_['data']['url']).stem.split("_")[0] == ror_id]
        ror_done_annots = [_ for _ in fpNER_annots if Path(_['data']['url']).stem.split("_")[0] == ror_id]
        png_id_to_annotate = get_pngid_to_annotate_balanced(ror_done_annots, ror_bba)
    else:
        for ror_id in RORs:
            ror_bba = [_ for _ in bba_annots if Path(_['data']['url']).stem.split("_")[0] == ror_id]
            ror_done_annots = [_ for _ in fpNER_annots if Path(_['data']['url']).stem == ror_id]
            png_id_to_annotate = get_pngid_to_annotate_balanced(ror_done_annots, ror_bba)

    # We send to fpNER only the images with BBOX annotations
    relevant_text = [
        cat_db.find_one(png_id+'_fitz', collection='cc_text')
        for png_id in png_id_to_annotate
        ]

    for text_obj in relevant_text:
        text_obj['url'] = f"https://24.91.161.49/58960_images/"+text_obj['png_id']+".png"

    # making sure no duplicates have been added
    done_img_ids = set([Path(_['data']['url']).stem  for _ in fpNER_annots])
    original_len = len(relevant_text)
    relevant_text = [_ for _ in relevant_text if _['png_id'] not in done_img_ids]

    post_LS(fpNER_PROJ_ID, relevant_text)

    print(f"{len(relevant_text)} has been added to fpNER project")
    print(f"{len(relevant_text) - original_len} duplicates have been removed in the process")

if __name__ == "__main__":
    main()