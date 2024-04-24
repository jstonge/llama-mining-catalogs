from pathlib import Path
import argparse
from helpers import get_annotations
import json

def parse_args():
    parser = argparse.ArgumentParser("Data Downloader")
    parser.add_argument(
        "-o", "--output", type=Path, help="output directory", required=True
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    fpNER_PROJ_ID = 59149
    TARGET_LABELS = ['Number', 'Description', 'Title', 'Prerequisite', 'Credit']
    annots = get_annotations(fpNER_PROJ_ID)

    out = []
    for annot_obj in annots:
        res = annot_obj['annotations'][0]['result']
        json_we_want = {'Number': None, 'Department': None, 'Title': None, 'Description': None, 'Credit': None, 'Prerequisite': None}
        output = []
        for ann in res:
            # annot=res[0]
            end, val, start, label = ann['value'].values()
            label = label[0]
            if label == 'Course':
                course_obj = {}
                for annot_sub in res:
                    start_sub = annot_sub['value']['start']
                    end_sub = annot_sub['value']['end']
                    label_sub = annot_sub['value']['labels'][0]
                    if label_sub in TARGET_LABELS:
                        if start_sub >= start and end_sub <= end:
                            if label_sub in course_obj:
                                ", ".join([course_obj[label_sub], annot_sub['value']['text']])
                            else:
                                course_obj[label_sub] = annot_sub['value']['text']
                output.append(course_obj)

        out.append({
            'file_name': annot_obj['data']['png_id'],
            'prompt': annot_obj['data']['text'],
            'completion': output
        })
    
    with open(args.output / 'fpNER_annots.json', 'w') as f:
        json.dump(out, f, indent=4)