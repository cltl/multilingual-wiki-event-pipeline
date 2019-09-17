
cd ..
here=$PWD

mkdir -p log
mkdir -p log/v1

#python main.py -> log/v1/extraction.out 2> log/v1/extraction.err

#python analyze.py -> log/v1/analysis.out 2> log/v1/analysis.err 

#cd /home/postma/Dutch_FrameNet_Lexicon/resources/run_open-sesame
#bash run_open_sesame.sh

find /home/postma/Dutch_FrameNet_Lexicon/resources/run_open-sesame/output/NAF/ -name '*naf' -exec cp {} wiki_output/en \; 


cd $here
#python enrich_classes.py --bin_folder="bin" --verbose=2
