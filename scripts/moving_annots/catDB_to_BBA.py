import argparse
from pathlib import Path
import Image
import io
from tqdm import tqdm

import json

import kitty
from kitty import InvalidCatId
import math
import numpy as np

from helpers import (
    get_annotations, 
    post_LS, 
    annotate_page
)

def parse_args():
    parser = argparse.ArgumentParser("Data Downloader")
    parser.add_argument(
        "--N_TOT_CATALOG",
        type=int,
        default=30,
        help="JSONlines file with urls and hashes",
        required=False,
    )
    parser.add_argument(
        "--PAGE_PER_CAT",
        type=int,
        default=20,
        required=False,
    )
    parser.add_argument(
        "--skip_pages",
        type=int,
        default=10,
        required=False,
        help="How many pages to skip in the beginning of the PDF",
    )
    return parser.parse_args()

def implement_sampling_strategy(self, n_tot_catalog, inst_obj):
    # Find relevant PDF ids. There could be more methods.
    min_year = min([c['start_year'] for c in inst_obj])
    max_yr = max([c['end_year'] for c in inst_obj])
    decades = list(range((min_year-min_year%10), max_yr+1, 10))

    # We ceil because we want to make sure we have at least N_TOT_CATALOG
    n_tot_catalog = math.ceil(n_tot_catalog / len(decades))

    rdm_pdf_id = []
    for i in range(len(decades)-1):
            min_yr, max_yr = decades[i], decades[i+1]
            potential_ids = {c['id'] for c in inst_obj if c['start_year'] >= min_yr and c['end_year'] <= max_yr}

            # WE MAKE SURE TEXT HAS BEEN PARSED FOR THAT CATALOG
            nb_hits = 0
            while potential_ids and nb_hits < n_tot_catalog:
                    random_pdf_id = np.random.choice(list(potential_ids), 1)[0]
                    potential_ids.remove(random_pdf_id)
                    try:
                            if self.cat_db.find_one(random_pdf_id, "pdf_id", 'cc_text' ):
                                    rdm_pdf_id.append(random_pdf_id)
                                    nb_hits += 1
                    except InvalidCatId:
                            pass
    return rdm_pdf_id

def main(ror_id, annotate=True):
        """
        catDB -> BBA

        Can be rerun many times. We make sure to not sample  already annotated pages from BBA.
        """
        args = parse_args()

        cat_db = kitty.CatalogDB()
        
        ror_id = args.ror
    
        BBA_PROJ_ID = 58960


        # Saving PNGs to send over to Juni's laptop.
        current_dir = Path()
        output_dir = current_dir / (BBA_PROJ_ID+"_images")
        output_dir.mkdir(exist_ok=True)

        # Checking if we have already annotated some of the pages
        coco = get_annotations(BBA_PROJ_ID, 'COCO')
        done_pngids = [Path(_['file_name']).stem for _ in coco['images']]

        # Hardecoded for now. We grab 30 x 20 = 600 pages because most of it might
        # not contain course objects. If we expect something like 20% of pages to
        # contain courses, then we have 120annots/institution.
        N_TOT_CATALOG = args.N_TOT_CATALOG
        PAGE_PER_CAT = args.PAGE_PER_CAT
        MIN_PAGE = args.skip_pages

        inst = cat_db.find(ror_id, "inst_id", "cc_catalog")

        # We want cat_type to be ug, gr, or both as they are often the main catalogs.
        # Same for semester being None (we get rid of summer semester)
        # We keep all the colleges
        # But be mindful that could ask something else for some institutions.
        filtered_inst = [
                c for c in inst if
                c['cat_type'] in ['ug', 'gr', 'both']
                # and c['college'] is None
                and c['semester'] is None
        ]

        rdm_pdf_id = implement_sampling_strategy(N_TOT_CATALOG, filtered_inst) # Note we don't double check if PDF has been annotated

        # For each PDF id, sample a given number of pages
        out = []
        for pdf_id in tqdm(rdm_pdf_id, total=len(rdm_pdf_id)):
                # grab PDF metadata to know number of pages
                pdf_obj = cat_db.find_one(pdf_id, collection="cc_pdf")

                # Do not select fewer pages to sample than we have
                NB_PAGE_TO_SAMPLE = PAGE_PER_CAT if PAGE_PER_CAT <= pdf_obj['tot_pages'] else pdf_obj['tot_pages']
                TRUE_MIN_PAGE = MIN_PAGE if MIN_PAGE <= pdf_obj['tot_pages'] else 0

                # random pages in the PDF but check if they were already done in BBA
                done_pages_in_pdf = set([int(_.split('_')[-1]) for _ in done_pngids if _.rsplit('_', 1)[0] == pdf_id])
                potential_pages = set(range(TRUE_MIN_PAGE, pdf_obj['tot_pages'])) - done_pages_in_pdf

                # at some point we'll miss pages... but might take a while
                rdm_pages = np.random.choice(list(potential_pages), NB_PAGE_TO_SAMPLE)

                # For each page, we will grab the PNG and the text and preannotate if flagged
                done_pngs = []
                for page in rdm_pages:
                        # Grab PNG of that page
                        png_id = f"{pdf_id}_{page}"
                        if png_id not in done_pngs:
                                png_obj = cat_db.find_one_gridfs(png_id, collection="cc_png")
                                if png_obj is not None:

                                        # CHECK if text is available
                                        text_obj = cat_db.find_one(f"{pdf_id}_fitz_token_pos_{page}", collection="cc_text")
                                        # for extracting text
                                        if len(json.loads(text_obj['text'])['tokens']) > 0:

                                                pdf_token = json.loads(text_obj['text'])

                                                with open(output_dir / f"{pdf_id}_{page}.png", "wb") as f:
                                                        f.write(png_obj)

                                                png_data = {
                                                        'data': {
                                                                'url': f"https://24.91.161.49/{output_dir}/{png_id}.png",
                                                                'png_id': png_id
                                                                }
                                                }

                                                if annotate:
                                                        result, extracted_text = annotate_page(png_obj, pdf_token)

                                                        # save that in predictions field, needs to match label studio schema
                                                        png_data['predictions'] = [{
                                                                'model_version': "one",
                                                                'score': 0.5,
                                                                'result':result
                                                                }]

                                                        png_data['data']['text'] = extracted_text

                                                out.append(png_data)
                                                done_pngs.append(png_id)



                                        else:
                                                print(f"Png is there but {pdf_id}_{page} has not text")
                                else:
                                        print(f"missing {pdf_id}_{page} Png")

        # assert len(out) >= (N_TOT_CATALOG * PAGE_PER_CAT) - 150, f"Expected at least {(N_TOT_CATALOG * PAGE_PER_CAT)-150} pages, got {len(out)}"
        post_LS(BBA_PROJ_ID, out)
