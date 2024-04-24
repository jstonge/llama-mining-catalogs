from typing import List, Any, Union, Dict, ClassVar
import requests
import json
import io
import zipfile
from pathlib import Path
from tqdm import tqdm
import Image
import os
from random import random
from collections import Counter
import math

import kitty

try:
    import torch
    is_cuda = torch.cuda.is_available()
except:
    is_cuda = False

cat_db = kitty.catDB()
    
def load_layout_model():
    try:
        import layoutparser as lp
        import torch

        MODEL_DIR = Path("../training/layout-model/outputs")
        best_bbox_model_id = "457000"

        return lp.Detectron2LayoutModel(
                config_path = str(MODEL_DIR/ best_bbox_model_id /  "config.yaml"),
                model_path = str(MODEL_DIR / best_bbox_model_id / "model_final.pth"),
                extra_config = ["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8],
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
        )
    except ImportError:
        raise ImportError("layout_model not working")

def post_LS(proj_id, data):
    """similar to update?"""
    response = requests.post(f'https://app.heartex.com/api/projects/{proj_id}/import', 
                            headers={'Content-Type': 'application/json', 'Authorization': f"Token {self.LS_TOK}"}, 
                            data=json.dumps(data), verify=False)
    print(response.status_code)

def get_annotations(proj_id, type='JSON', only_annots=True):
        """Find most recent annotations of a given project id."""
        headers = { "Authorization": f"Token {os.environ.get('LS_TOK')}" }
        base_url = "https://app.heartex.com/api/projects"
        
        if type == 'JSON':
            url = f"{base_url}/{proj_id}/export?exportType=JSON&download_all_tasks=true"
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                json_data = json.loads(response.text)
                
                if only_annots:
                    return [_ for _ in json_data if len(_['annotations']) > 0]
                else:
                    return json_data
                
        elif type == 'COCO':
            url = f"{base_url}/58960/exports/"
            response = requests.get(url, headers=headers)

            # USE LS STUDIO UI TO CREATE SNAPSHOT ID. For some reasons API call is not working well.
            print("Did you make sure to have created the snapshot that you want?")
            export_pk = json.loads(response.text)[0]['id']

            url = f"{base_url}/58960/exports/{export_pk}/download?exportType=COCO"
            response = requests.get(url,  headers=headers)
            
            if response.status_code == 200:
                binary_data = response.content
                with io.BytesIO(binary_data) as binary_file:
                    with zipfile.ZipFile(binary_file, 'r') as zip_file:
                        json_file_name = zip_file.namelist()[1]  # Adjust as necessary
                        with zip_file.open(json_file_name) as json_file:
                            json_data = json.loads(json_file.read().decode('utf-8'))
                
                # !TODO: why do some images on LS do not have sizes? It should.
                for img_obj in tqdm(json_data['images']):
                    
                    w, h, _, fname = img_obj.values()
                    if w == h == None:
                        png_id = Path(fname ).stem
                        img = cat_db.find_one_gridfs(png_id, collection="cc_png")
                        img = Image.open(io.BytesIO(img))
                        
                        width, height = img.size
                        img_obj['width'] = width
                        img_obj['height'] = height
                
                return json_data
                                
            else:
                print(f"Failed to fetch data: {response.status_code}")

def resize_bbox(original_size, new_size, bbox):
    """
    Resize label-studio page dimension with mongodb page dimension
    original size: page dimension (width, height) in Label-studio
    new_size: page dimensino (width, height) in Mongodb
    bbox: bounding box coordinates (x, y, w, h)
    """
    # Original bbox coordinates
    x, y, w, h = bbox

    # Calculate scale factors
    scale_width = new_size[0] / original_size[0]
    scale_height = new_size[1] / original_size[1]
    
    # Scale bbox coordinates
    new_x = x * scale_width
    new_y = y * scale_height
    new_w = w * scale_width
    new_h = h * scale_height

    return [new_x, new_y, new_w, new_h]

def extract_text(pdf_token, bbox):

    """
    Extract text from a given pdf_token (info about excat token
    positions on a page) and bbox (location of relevant text)
    params
    ======
        pdf_token:
            {page: {width: float, height: float, index: int},
            tokens: List[{
                text': int, x: float, width: float,
                y: float, height: float, id: 0},
                ...
            ]}
        bbox: (x,y,w,h)
    """
    def _is_point_inside_bbox(row, bbox):
        px, py = row['x'], row['y']
        x1, y1, x2, y2 = bbox
        return x1 <= math.ceil(px) <= x2 and y1 <= math.ceil(py) <= y2
    
    for j, tok in enumerate(pdf_token['tokens']):
        tok['id'] = j
    
    x, y, w, h = bbox
    # y = math.floor(y)
    x = math.floor(x)
    w = math.ceil(w)
    h = math.ceil(h)
    bbox = x, y, w + x, h + y #x1, y1, x2, y2
    
    bib_tokens = list(filter(lambda row: _is_point_inside_bbox(row, bbox), pdf_token['tokens']))

    return ' '.join([_['text'] for _ in bib_tokens])

def annotate_page(png_obj, pdf_token):
    layout_model = load_layout_model()
    img = Image.open(io.BytesIO(png_obj))
    layout = layout_model.detect(img)
    # WE SKIP PAGES WITH NO PREDICTIONS

    if len(layout) == 0:
        print(f"skipping")
        return None

    # for each prediction on that page
    result = []
    extracted_text = []
    for i in range(len(layout)):
            height=layout[i].block.y_2-layout[i].block.y_1
            width=layout[i].block.x_2-layout[i].block.x_1
            result.append({
                    "id": f"result{i+1}",
                    "type":"rectanglelabels",
                    "from_name": "label", "to_name": "image",
                    "original_width": img.width,
                    "original_height": img.height,
                    "image_rotation": 0,
                    "value": {
                            "rotation": 0,
                            "x": (layout[i].block.x_1 / img.width) * 100,
                            "y": (layout[i].block.y_1 / img.height) * 100,
                            "width": (width / img.width) * 100,
                            "height": (height / img.height) * 100,
                            "rectanglelabels": ["course"]
                    }
            })

            # get text from the page
            bbox = layout[i].block.x_1, layout[i].block.y_1, width, height
            mongodb_size = (pdf_token['page']['width'], pdf_token['page']['height'])
            resized_bbox = resize_bbox((img.width, img.height), mongodb_size, bbox)
            extracted_text.append(extract_text(pdf_token, resized_bbox))

    return result, extracted_text

def get_pngid_to_annotate_balanced(self, done_proj_annots, bba_annots):
    """We only balance by decade, annots should be filtered by institution beforehand"""
    annots_start_yr = Counter([_['data']['png_id'].split("_")[2] for _ in done_proj_annots])
    # To keep track of how many annotations has been done by decade
    annots_by_decade = {}
    for dec,v in annots_start_yr.items():
        decade = int(dec) - int(dec)%10
        if annots_by_decade.get(decade) is None:
            annots_by_decade[decade] = v
        else:
            annots_by_decade[decade] += v
    # WE BALANCE THE ANNOTATIONS BY DECADE FOR THAT INSTITUTION
    min_val = min(annots_by_decade.values())
    min_yr = min([int(_['data']['url'].split("/")[-1].split("_")[2]) for _ in bba_annots ])
    max_yr = max([int(_['data']['url'].split("/")[-1].split("_")[3]) for _ in bba_annots ])
    decades = list(range((min_yr-max_yr%10), 2030, 10))
    done_ids = {_['data']['png_id'] for _ in done_proj_annots}

    # FOR EACH DECADE
    png_id_to_annotate = []
    for i in range(len(decades)-1):
        min_yr, max_yr = decades[i], decades[i+1]
        potential_ids = {Path(_['data']['url']).stem for _ in bba_annots
            if int(_['data']['url'].split("/")[-1].split("_")[2]) > min_yr and
            int(_['data']['url'].split("/")[-1].split("_")[3]) < max_yr
        }

        # MAKING SURE WE DON'T REANNOTATE SAME DOCUMENTS
        potential_ids = potential_ids - done_ids
        MIN_SAMPLE = 2 if len(potential_ids) >= 2 else len(potential_ids)
        CURRENT_COUNT = decades[i] if annots_by_decade.get(decades[i]) else 0

        # IF HAVE DONE ENOUGH OF THAT DECADE, SKIP IT. Cutoff is a magic number at the moment.
        if MIN_SAMPLE > 0 and CURRENT_COUNT <= min_val+4:
            png_id_to_annotate += list(random.sample(potential_ids, MIN_SAMPLE))

    return png_id_to_annotate

