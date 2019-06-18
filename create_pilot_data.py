"""
Create folder with pilot data

Usage:
  create_pilot_data.py --input_folder=<input_folder> --output_folder=<output_folder> --spacy_models=<spacy_models> --folder_secondary_texts=<folder_secondary_texts> --layers=<layers> --readme_path=<readme_path>

Options:
    --input_folder=<input_folder> all files with *bin will be used
    --output_folder=<output_folder> the output folder
    --spacy_models=<spacy_models> models to use, e.g., "EN-en;NL-nl_core_news_sm;IT:it_core_news_sm"
    --folder_secondary_texts=<folder_secondary_texts> folder with json with manually selected secondary reference texts (development/secondary_reference_texts.json)
    --layers=<layers> NAF layers to add, e.g, "raw-text-terms"
    --readme_path=<readme_path> path to README

Example:
    python create_pilot_data.py --input_folder="bin" --output_folder="pilot_data" \
    --spacy_models="en-en;nl-nl_core_news_sm;it-it_core_news_sm" \
    --folder_secondary_texts="development" \
    --layers="raw-text-terms" --readme_path="wdt_fn_mappings/PILOT_README.md"
"""
from docopt import docopt
from glob import glob
import pickle
import json
import shutil
import datetime
import os
from path import Path
import spacy
import datetime
from classes import ReferenceText

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

secondary_texts_folder = Path(arguments['--folder_secondary_texts'])
secondary_texts = json.load(open(str(secondary_texts_folder / 'secondary_reference_texts.json')))


# load spaCy models
models = {}
for model_info in arguments['--spacy_models'].split(';'):
    language, model_name = model_info.split('-')
    models[language] = spacy.load(model_name)

# processing
incident_id2incident_info = {}

for bin_file in glob(f'{input_folder}/*.bin'):

    # use date of file for dct of reference texts
    file_info = os.stat(bin_file)
    dct = datetime.datetime.fromtimestamp(file_info.st_ctime)

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

        if incident.wdt_id in secondary_texts:
            sec_ref_texts_info = secondary_texts[incident.wdt_id]
            for sec_ref_text_info in sec_ref_texts_info:
                path = secondary_texts_folder / 'secondary_reference_texts' / f'{sec_ref_text_info["title"]}.txt'
                assert path.exists(), f'{path} does not exist'
                with open(str(path)) as infile:
                    raw = infile.read()

                day, month, year = sec_ref_text_info['dct'].split('-')
                date = datetime.date(int(year), int(month), int(day))

                ref_text_obj = ReferenceText(wiki_uri=sec_ref_text_info['uri'],
                                             name=sec_ref_text_info['title'],
                                             language=sec_ref_text_info['language'],
                                             wiki_content=raw,
                                             creation_date=date)

                incident.reference_texts.append(ref_text_obj)


        for ref_text_obj in incident.reference_texts:
            if ref_text_obj.language in models:

                assert ref_text_obj.wiki_uri
                naf_output_path = naf_folder / f'{ref_text_obj.name}.naf'

                if ref_text_obj.creation_date:
                    dct_to_use = ref_text_obj.creation_date # actual publish date
                else:
                    dct_to_use = dct # date of crawling is used

                root = ref_text_obj.process_spacy_and_convert_to_naf(models[ref_text_obj.language],
                                                                     dct_to_use,
                                                                     layers,
                                                                     output_path=str(naf_output_path))
                ref_text_info = {
                    'language' : ref_text_obj.language,
                    'title' : ref_text_obj.name,
                    'url': ref_text_obj.wiki_uri,
                    'raw' : root.find('raw').text,
                    'naf_basename' : f'{ref_text_obj.name}.naf',
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