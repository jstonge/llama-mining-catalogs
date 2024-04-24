#
# Makefile for the LLM catalog mining experiments
#
# Author: JSO
# Date: 2024-04-24
#

DATA_DIR=$(realpath ./data)
DATA_DIR_RAW=$(DATA_DIR)/raw
DATA_DIR_CLEAN=$(DATA_DIR)/clean

FRAMEWORK_DIR=$(realpath ./docs)
DATA_DIR_OBS=$(FRAMEWORK_DIR)/data

SCRIPT_DIR=./src
MV_ANNOTS_SCRIPTS=$(SCRIPT_DIR)/moving_annots

UVM_ROR=0155zta11
CMU_ROR=05x2bcf33
UCLA_ROR=046rm7j60

#####################
#                   #
#       GLOBAL      #
#                   #
#####################

clean:
	rm -rf docs/.observablehq/cache

available_ror:
	echo uvm:$(UVM_ROR) cmu:$(CMU_ROR) ucla:$(UCLA_ROR)

####################################
#                                  #
#        ANNOTATION PIPELINE       #
#                                  #
####################################

# Original annotated data.
# We annotate 30 catalogs, each with 20 pages, for each institution.
# The draws are random across decades
N_TOT_CATALOG=30
PAGE_PER_CAT=20
SKIP_PAGES=10

# When we want to add annotation, we add 100 pages at a time, 
# each with 5 course. 
# In BBA project, we know the how many courses per page.
n_pages=100
course_obj_per_page=5

.PHONY: bba_to_cner bba_to_fpner bba

# cat_db_to_bba was use once to grab the data from the catDB.
# It is not used in the remainder of this makefile.
cat_db_to_bba:
	python $(MV_ANNOTS_DIR)/cat_db_to_bba.py --n_tot_catalog $(N_TOT_CATALOG) \
											 --page_per_cat $(PAGE_PER_CAT) \
											 --skip_pages $(SKIP_PAGES)

bba_to_cner: 
	python $(MV_ANNOTS_DIR)/BBA_to_cNER.py --ror $(ROR) \
										   --n_pages $(n_pages) \
										   --course_obj_per_page $(course_obj_per_page)

# For now, we simply push all the data from BBA to fpNER (REA).
# Then we balance fpNER project using another function.
bba_to_fpner: 
	python $(MV_ANNOTS_DIR)/BBA_to_fpNER.py


####################################
#                                  #
#        TRAIN-TEST SPLIT          #
#                                  #
####################################

prepare_fpNER:
	python $(SCRIPT_DIR)/prepare_fpNER.py -o $(DATA_DIR_CLEAN)

kfold_split:
	python $(SCRIPT_DIR)/prepare_fpNER.py -i $(DATA_DIR_CLEAN) \
		-o $(DATA_DIR_CLEAN)

#########################
#                       #
#        TRAINING       #
#                       #
#########################

#!TODO

#############################
#                           #
#        BENCHMARKING       #
#                           #
#############################

#!TODO