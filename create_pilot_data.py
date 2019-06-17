"""
Create folder with pilot data

Usage:
  create_pilot_data.py --input_folder=<input_folder> --output_folder=<output_folder> --spacy_models=<spacy_models> --layers=<layers> --readme_path=<readme_path>

Options:
    --input_folder=<input_folder> all files with *bin will be used
    --output_folder=<output_folder> the output folder
    --spacy_models=<spacy_models> models to use, e.g., "EN-en;NL-nl_core_news_sm;IT:it_core_news_sm"
    --layers=<layers> NAF layers to add, e.g, "raw-text"
    --readme_path=<readme_path> path to README

Example:
    python create_pilot_data.py --input_folder="bin" --output_folder="pilot_data" \
    --spacy_models="en-en;nl-nl_core_news_sm;it-it_core_news_sm" --layers="raw-text" --readme_path="wdt_fn_mappings/PILOT_README.md"
"""
from docopt import docopt
from glob import glob
import pickle
import json
import shutil
from path import Path
import spacy
import spacy_to_naf

# load arguments
arguments = docopt(__doc__)
print()
print('PROVIDED ARGUMENTS')
print(arguments)
print()

layers = set(arguments['--layers'].split('-'))
input_folder = arguments['--input_folder']
output_folder = Path(arguments['--output_folder'])
if output_folder.exists():
    shutil.rmtree(str(output_folder))
output_folder.mkdir()
naf_folder = output_folder / 'naf'
naf_folder.mkdir()
main_json_output_path = output_folder / 'incidents.json'

# load spaCy models
models = {}
for model_info in arguments['--spacy_models'].split(';'):
    language, model_name = model_info.split('-')
    models[language] = spacy.load(model_name)

# processing
incident_id2incident_info = {}

for bin_file in glob(f'{input_folder}/*.bin'):
    incident_collection = pickle.load(open(bin_file, 'rb'))

    for incident in incident_collection.incidents:
        info = {
            'reference_texts' :
                {language : []
                 for language in models},
            'event_type' : incident.incident_type,
            'meta_data' : {key: list(value)
                           for key, value in incident.extra_info.items()
                           }
        }

        for ref_text_obj in incident.reference_texts:
            if ref_text_obj.language in models:
                root = spacy_to_naf.text_to_NAF(text=ref_text_obj.wiki_content,
                                                nlp=models[ref_text_obj.language],
                                                layers=layers,
                                                language=ref_text_obj.language)

                naf_output_path = naf_folder / f'{ref_text_obj.name}.naf'
                with open(str(naf_output_path), 'w') as outfile:
                    outfile.write(spacy_to_naf.NAF_to_string(NAF=root))

                ref_text_info = {
                    'language' : ref_text_obj.language,
                    'naf_basename' : f'{ref_text_obj.name}.naf',
                    'raw' : root.find('raw').text,
                }

                info['reference_texts'][ref_text_obj.language].append(ref_text_info)
        incident_id2incident_info[incident.wdt_id] = info

with open(str(main_json_output_path), 'w') as outfile:
    print(f'saved to {main_json_output_path}')
    print(f'number of incidents: {len(incident_id2incident_info)}')
    print('spaCy language models used:')
    for lang, nlp in models.items():
        print(f'spaCy-{nlp.meta["version"]}_language-{lang}_model-{nlp.meta["name"]}')
    json.dump(incident_id2incident_info, outfile, indent=4, sort_keys=True)

with open(arguments['--readme_path']) as infile:
    readme_text = infile.read()

readme_path = output_folder / 'README.md'
with open(str(readme_path), 'w') as outfile:
    outfile.write(readme_text)