import shutil
import time
import spacy
import os
from pprint import pprint
import pickle
from tqdm import tqdm
import json
from collections import defaultdict
from datetime import datetime
import pandas as pd

import pilot_utils
import native_api_utils
import classes
import config
import utils
import wikipedia_utils as wu

incident_types=config.incident_types

def add_wikipedia_pages_from_api(incidents, wdt_ids, raw_results):
    assert(len(wdt_ids)>0)
    id_batches=utils.split_in_batches(wdt_ids, 50)

    for index, batch in enumerate(id_batches):
        wiki_pages=native_api_utils.obtain_wiki_page_titles(batch, languages)
        for incident in incidents:
            if incident.wdt_id in wiki_pages.keys():
                incident_wikipedia=wiki_pages[incident.wdt_id]
                for language, name in incident_wikipedia.items():
                    found=False
                    for rt in incident.reference_texts:
                        if rt.name==name and rt.language==language:
                            rt.found_by.append('API')
                            found=True
                    if not found:
                        ref_text=classes.ReferenceText(
                                    name=name,
                                    language=language,
                                    found_by=['API']
                                )
                        incident.reference_texts.append(ref_text)
    return incidents

def retrieve_incidents_per_type(type_qid, type_label, limit=10):
    """
    Given an event type identifier, retrieve incidents that belong to this type.
    """
    eventtype2json=config.qid2fn

    if type_qid in eventtype2json:
        jsonfilename='wdt_fn_mappings/%s.json' % eventtype2json[type_qid]
    else:
        jsonfilename='wdt_fn_mappings/any.json'
    with open(jsonfilename, 'rb') as f:
        wdt_fn_mappings_COL=json.load(f)

    incidents=[]
    print("\n### 1. ### Retrieving and storing wikidata information from SPARQL...")
    results_by_id=utils.construct_and_run_query(type_qid, languages, wdt_fn_mappings_COL, limit)
    wdt_ids=[]
    if not len(results_by_id.items()):
        return [], ''
    for full_wdt_id, inc_data in results_by_id.items():
        extra_info=inc_data['extra_info']
        direct_types={direct_type.replace('http://www.wikidata.org/entity/', 'wd:')
                      for direct_type in inc_data['direct_types']}
        wdt_id=full_wdt_id.split('/')[-1]
        wdt_ids.append(wdt_id)

        ref_texts=[]
        for language, name in inc_data['references'].items():
            ref_text=classes.ReferenceText(
                        name=name,
                        language=language,
                        found_by=['SPARQL']
                    )
            ref_texts.append(ref_text)

        incident=classes.Incident(
                incident_type=type_label,
                wdt_id=wdt_id,
                direct_types=direct_types,
                extra_info=extra_info,
                reference_texts=ref_texts
            )
        incidents.append(incident)
    inc_type_uri=inc_data['type_id']
    print("Wikidata querying and storing finished. Number of incidents:", len(incidents))
    print('\n### 2. ### Enriching the reference texts through the Wikipedia-Wikidata API...')
    incidents=add_wikipedia_pages_from_api(incidents, wdt_ids, results_by_id)
    print('API querying done. Number of incidents:', len(incidents))
    return incidents

def obtain_reference_texts(incidents, wiki_folder, wiki_uri2path_info, language2info):
    print('\n### 3. ### Retrieve reference text information: text and entity annotations from the local version of Wikipedia.')
    new_incidents=[]
    for incident in tqdm(incidents):
        new_reference_texts=[]
        for ref_text in incident.reference_texts:
            language=ref_text.language
            wiki_title=ref_text.name

            prefix = language2info[ref_text.language]['prefix']

            text, annotations, success, reason = wu.load_wiki_page_info(wiki_title,
									prefix,
									language,
									wiki_folder,
                                                                        wiki_uri2path_info)

            if success:
                ref_text.annotations=annotations
                ref_text.content=text
                new_reference_texts.append(ref_text)
        new_reference_texts=utils.deduplicate_ref_texts(new_reference_texts)

        if len(new_reference_texts): # if there are reference texts with text, try to get more data by using the Wiki langlinks info we have stored.
            incident.reference_texts=new_reference_texts
            new_incidents.append(incident)
    print('Retrieval of reference texts done. Number of incidents:', len(new_incidents))
    return new_incidents

def get_primary_rt_links(incidents):
    for incident in tqdm(incidents):
        for ref_text in incident.reference_texts:
            ext_links=native_api_utils.obtain_primary_rt_links(ref_text.name, ref_text.language)
            if ext_links:
                ref_text.primary_ref_texts=ext_links
    return incidents

if __name__ == '__main__':

    
    start_init=time.time()

    wiki_folder = '../Wikipedia_Reader/wiki'
    naf_output_folder = 'wiki_output'
    rdf_folder = 'rdf'
    bin_folder= 'bin'

    utils.remove_and_create_folder(rdf_folder)
    utils.remove_and_create_folder(naf_output_folder)
    utils.remove_and_create_folder(bin_folder)

    print('NAF, RDF, and BIN directories have been re-created')
    
    # load index and language info
    path_uri2path_info = os.path.join(wiki_folder, 'page2path.p')
    with open(path_uri2path_info, 'rb') as infile:
        wiki_uri2path_info = pickle.load(infile) # make take some time

    language_info_path = os.path.join(wiki_folder, 'language2info.json')
    with open(language_info_path, 'r')  as infile:
        language2info = json.load(infile)

    print("Wikipedia indices loaded")

    wiki_langlinks_path = 'resources/Wikipedia_langlinks/resources/wikipedia-parallel-titles/output/merged_indices.p'
    with open(wiki_langlinks_path, 'rb') as infile:
        wiki_langlinks = pickle.load(infile)

    print('Wikipedia parallel titles loaded')

    # load spaCy models
    spacy_models = "en-en_core_web_sm;nl-nl_core_news_sm;it-it_core_news_sm"
    models = {}
    for model_info in spacy_models.split(';'):
        language, model_name = model_info.split('-')
        models[language] = spacy.load(model_name)

    print("Spacy models have been loaded.")

    end_init=time.time()
    print('Init phase done. Time needed to initialize the extractor', utils.format_time(end_init-start_init), 'sec')

    all_inc_stats=[]

    languages=config.languages_list

    for incident_type_uri in incident_types:

        incident_type=""

        pilot_and_languages=languages + ['pilot']

        inc_stats=[incident_type_uri, ','.join(languages)]

        print('\n\n\n')
        print('----- INCIDENT TYPE: %s -----' % incident_type_uri) 
        print('\n\n')

        start = time.time()

        # Query SPARQL and the API to get incidents, their properties, and labels.
        incidents=retrieve_incidents_per_type(incident_type_uri, incident_type, 99999)

        if not len(incidents):
            print('NO INCIDENTS FOUND FOR %s. Continuing to next type...')
            continue

        new_incidents=obtain_reference_texts(incidents, wiki_folder, wiki_uri2path_info, language2info)

        collection=classes.IncidentCollection(incidents=new_incidents,
                                 incident_type=incident_type,
                                 incident_type_uri=incident_type_uri,
                                 languages=languages)

        output_file=utils.make_output_filename(bin_folder, 
                                                incident_type_uri, 
                                                languages)
        
        with open(output_file, 'wb') as of:
            pickle.dump(collection, of)

        inc_stats.append(len(collection.incidents))

        ttl_filename = '%s/%s_%s.ttl' % (rdf_folder, incident_type_uri, '_'.join(languages))
        collection.serialize(ttl_filename)

        after_extraction = time.time()

        pilots=pilot_utils.create_pilot_data(collection)

        after_pilot_selection=time.time()

        pilots=get_primary_rt_links(pilots)

        after_primary_texts=time.time()

        pilot_collection=classes.IncidentCollection(incidents=pilots,
                                                     incident_type_uri=incident_type_uri,
                                                     incident_type=incident_type,
                                                     languages=languages)

        out_file=utils.make_output_filename(bin_folder, incident_type_uri, pilot_and_languages)

        with open(out_file, 'wb') as of:
            pickle.dump(pilot_collection, of)

        ttl_filename = '%s/%s_%s_pilot.ttl' % (rdf_folder, incident_type_uri, '_'.join(pilot_and_languages))
        pilot_collection.serialize(ttl_filename)

        #assert len(pilot_collection.incidents)>0, 'No pilot incidents for type %s' % incident_type
        if len(pilot_collection.incidents)==0:
            print('No pilot incidents for type %s' % incident_type_uri)
        else:
            print('start pilot data processing', datetime.now())
        for incident_obj in pilot_collection.incidents:
            for ref_text_obj in incident_obj.reference_texts:
                wiki_title = ref_text_obj.name
                language = ref_text_obj.language
                annotations=ref_text_obj.annotations
                text=ref_text_obj.content
                uri=ref_text_obj.uri

                prefix = language2info[language]['prefix']

                year, month, day = language2info[language]['year_month_day']
                dct = datetime(year, month, day)

                nlp = models[language]

                pilot_utils.text_to_naf(wiki_title,
                            text,
                            uri,
                            annotations,
                            prefix,
                            language,
                            nlp,
                            dct,
                            output_folder=naf_output_folder,
                            wiki_langlinks=wiki_langlinks)
        inc_stats.append(len(pilot_collection.incidents))

        end=time.time()

        inc_stats.append(utils.format_time(after_extraction-start))
        inc_stats.append(utils.format_time(after_pilot_selection-after_extraction))
        inc_stats.append(utils.format_time(after_primary_texts-after_pilot_selection))
        inc_stats.append(utils.format_time(end-after_primary_texts))
        inc_stats.append(utils.format_time(end-start))

        all_inc_stats.append(inc_stats)

    headers=['Type', 'Languages', '#incidents', '#pilot incidents', 'Time to extract incidents+RTs', 'Time to select pilot data', 'Time to get primary RT links', 'Time to run spacy, enrich, and store to NAF+RDF', 'Total time']

    df=pd.DataFrame(all_inc_stats, columns=headers)
    print(df.to_csv(index=False))

    print('TOTAL TIME TO RUN THE SCRIPT for', incident_types, ':', utils.format_time(end-start_init), 'sec')
