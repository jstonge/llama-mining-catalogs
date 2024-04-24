# Script Directory

The scripts are organized as follows:

1. `moving_annots/` contains scripts to facilitate annotation pipeline on label-studio (adding more annotations, balancing projects, etc.)
1. `preprocessing/` takes what is on label-studio and prepare the annotations to be in the right format for training.
1. `training/` contains git submodules for the different models used in our data pipeline. At the moment, this include a layout-model to detect course objects, and two foundation models that are fine-tuned on extracting all course objects on a single page or a single course object at a time.
1. `benchmarking/` benchmarks the different approaches. 