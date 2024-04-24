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
    load_layout_model, 
    resize_bbox, 
    extract_text
)

def parse_args():
    parser = argparse.ArgumentParser("Data Downloader")
    parser.add_argument("--ror", required=True)
    parser.add_argument("--n_pages", type=int, required=True)
    parser.add_argument("--course_obj_per_page", type=int, required=False)
    return parser.parse_args()

def main():

    args = parse_args()

    cat_db = kitty.CatalogDB()
    layout_model = load_layout_model()
    
    ror_id = args.ror
    
    BBA_PROJ_ID = 58960
    cNER_PROJ_ID = 60416
    n_page = args.n_pages
    course_obj_per_page = args.course_per_page
    bba_annots = get_annotations(BBA_PROJ_ID, 'JSON', only_annots=True)
    current_ner_annot = get_annotations(cNER_PROJ_ID, 'JSON', only_annots=True)

    ner_id_to_remove = set([annot['data']['png_id'] for annot in current_ner_annot]) # already done annotations.

    ror_id_to_keep = set([Path(annot['data']['url']).stem for annot in bba_annots
                            if Path(annot['data']['url']).stem.split("_")[0] == ror_id ])

    bba_annots = [
        annot for annot in bba_annots
        if Path(annot['data']['url']).stem in ror_id_to_keep and Path(annot['data']['url']).stem not in ner_id_to_remove
        ]

    # Page-level sampling strategy
    n_page = n_page if len(bba_annots) >= n_page else len(bba_annots)
    RDM_IMGS = np.random.choice(bba_annots, n_page, replace=False)

    relevant_text = []
    for img_path in RDM_IMGS:
        png_id = img_path['data']['png_id']
        split_fname=png_id.split("_")
        pdfid='_'.join(split_fname[:-1])
        page=split_fname[-1]

        text_obj = cat_db.find_one(f"{pdfid}_fitz_token_pos_{page}", collection="cc_text")
        pdf_token = json.loads(text_obj['text'])
        png_obj = cat_db.find_one_gridfs(png_id, collection='cc_png')
        img = Image.open(io.BytesIO(png_obj))

        layout = layout_model.detect(img)

        # Course-level sampling strategy
        MIN_SAMPLE = course_obj_per_page if len(layout) > course_obj_per_page else len(layout)
        SELECTED_COURSES  = sorted(np.random.choice(range(len(layout)), MIN_SAMPLE, replace=False))

        for i in SELECTED_COURSES:
            # when extracting text from bbox, make sure we are using same coordinates from mongodb
            mongodb_size = (pdf_token['page']['width'], pdf_token['page']['height'])
            height=layout[i].block.y_2-layout[i].block.y_1
            width=layout[i].block.x_2-layout[i].block.x_1
            bbox = layout[i].block.x_1, layout[i].block.y_1, width, height
            resized_bbox = resize_bbox((img.width, img.height), mongodb_size, bbox)

            relevant_text.append({
                'id': png_id+"_"+str(i),
                'text': extract_text(pdf_token, resized_bbox),
                'annotated': False,
                'catalog_id': None,
                'conversion': 'fitz',
                'inst_id': ror_id,
                'url': f"https://24.91.161.49/58960_images/{png_id}.png",
            })

    # CHECKS BEFORE SHIPPING TO LABEL STUDIO
    assert len([_['id'] for _ in relevant_text]) == len(set([_['id'] for _ in relevant_text]))

    # Dump data to annotate
    post_LS(cNER_PROJ_ID, relevant_text)


if __name__ == "__main__":
    main()