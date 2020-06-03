#!/usr/bin/env bash

python -m spacy download en_core_web_sm
python -m spacy download nl_core_news_sm
python -m spacy download it_core_news_sm

rm -rf resources
mkdir resources
cd resources

wget http://kyoto.let.vu.nl/~postma/dfn/mwep/merged_indices.p

git clone https://github.com/cltl/SpaCy-to-NAF
cp SpaCy-to-NAF/spacy_to_naf.py ../

wget http://kyoto.let.vu.nl/~postma/dfn/mwep/Wikipedia_Reader.zip
unzip Wikipedia_Reader.zip


