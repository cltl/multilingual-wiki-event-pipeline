#!/usr/bin/env bash

rm -f spacy_to_naf.py
wget https://raw.githubusercontent.com/cltl/SpaCy-to-NAF/master/spacy_to_naf.py

python -m spacy download en_core_web_sm
python -m spacy download nl_core_news_sm
python -m spacy download it_core_news_sm

rm -rf resources
mkdir resources
cd resources
git clone https://github.com/cltl/FN_Reader
cd FN_Reader
pip install -r requirements.txt
bash install.sh
cd ..
