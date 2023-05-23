"""
Run MWEP

Usage:
  main.py --config_path=<config_path>\
   --project=<project>\
   --path_event_types=<path_event_types>\
   --path_mapping_wd_to_sem=<path_mapping_wd_to_sem>\
   --languages=<languages>\
   --wikipedia_sources=<wikipedia_sources>\
   --verbose=<verbose>

Options:
    --config_path=<config_path>
    --project=<project> project name, e.g., pilot
    --path_event_types=<path_event_types> txt file, one event type per line, e.g., Q132821
    --path_mapping_wd_to_sem=<path_mapping_wd_to_sem> see wdt_fn_mappings/any.json as example
    --languages=<languages> languages separated by -, e.g., "nl-it-en"
    --wikipedia_sources=<wikipedia_sources> if "True", crawl Wikipedia sources
    --verbose=<verbose> 0 --> no stdout 1 --> general stdout 2 --> detailed stdout

Example:
    python main.py --config_path="config/mwep_settings.json"\
    --project="pilot"\
    --path_event_types="config/event_types.txt"\
    --path_mapping_wd_to_sem="wdt_fn_mappings/any.json"\
    --languages="nl-en"\
    --wikipedia_sources="False"\
    --verbose=1
"""
import json
import os
import pickle
import time
from datetime import datetime

import pandas as pd
import spacy
from tqdm import tqdm

import classes
import crawl_utils
import json_utils
import xml_utils
import native_api_utils
import pilot_utils
import utils
import wikipedia_utils as wu

for_encoding = 'é'

def add_wikipedia_pages_from_api(incidents, wdt_ids):
    assert (len(wdt_ids) > 0)
    id_batches = utils.split_in_batches(wdt_ids, 50)

    for index, batch in enumerate(id_batches):
        wiki_pages = native_api_utils.obtain_wiki_page_titles(batch, languages)
        for incident in incidents:
            if incident.wdt_id in wiki_pages.keys():
                incident_wikipedia = wiki_pages[incident.wdt_id]
                for language, name in incident_wikipedia.items():
                    found = False
                    for rt in incident.reference_texts:
                        if rt.name == name and rt.language == language:
                            rt.found_by.append('API')
                            found = True
                    if not found:
                        ref_text = classes.ReferenceText(
                            name=name,
                            language=language,
                            found_by=['API']
                        )
                        incident.reference_texts.append(ref_text)
    return incidents

def retrieve_incidents_per_participant(type_qid,
                                event_type_matching,
                                json_wd_to_sem,
                                limit=10):
    """
    Given an event type identifier, retrieve incidents that belong to this type.
    """
    with open(json_wd_to_sem, 'rb') as f:
        wdt_fn_mappings_COL = json.load(f)

    incidents = []
    print("\n### 1. ### Retrieving and storing wikidata information from SPARQL...")
    results_by_id = utils.construct_and_run_query(type_qid,
                                                  event_type_matching,
                                                  languages,
                                                  wdt_fn_mappings_COL,
                                                  limit)
    wdt_ids = []
    if not len(results_by_id.items()):
        return [], ''
    for full_wdt_id, inc_data in results_by_id.items():
        extra_info = inc_data['extra_info']
        direct_types = {direct_type.replace('http://www.wikidata.org/entity/', 'wd:')
                        for direct_type in inc_data['direct_types']}
        wdt_id = full_wdt_id.split('/')[-1]
        wdt_ids.append(wdt_id)

        ref_texts = []
        for language, name in inc_data['references'].items():
            ref_text = classes.ReferenceText(
                name=name,
                language=language,
                found_by=['SPARQL']
            )
            ref_texts.append(ref_text)

        incident = classes.Incident(
            incident_type=type_qid,
            wdt_id=wdt_id,
            direct_types=direct_types,
            extra_info=extra_info,
            reference_texts=ref_texts
        )
        incidents.append(incident)

    print("Wikidata querying and storing finished. Number of incidents:", len(incidents))
    ## debugging: store original incidents':
    all_incidents = dict()
    # print(type(incidents), type(type_qid))
    # print(type(incidentcs[5]))
    all_incidents[type_qid] = [inc.wdt_id for inc in incidents]
    with open('json/all_incidents.json', 'w') as outfile:
        json.dump(all_incidents, outfile)
    print('\n### 2. ### Enriching the reference texts through the Wikipedia-Wikidata API...')
    incidents = add_wikipedia_pages_from_api(incidents, wdt_ids)
    print('API querying done. Number of incidents:', len(incidents))
    return incidents

def retrieve_incidents_per_type(type_qid,
                                event_type_matching,
                                json_wd_to_sem,
                                limit=10):
    """
    Given an event type identifier, retrieve incidents that belong to this type.
    """
    with open(json_wd_to_sem, 'rb') as f:
        wdt_fn_mappings_COL = json.load(f)

    incidents = []
    print("\n### 1. ### Retrieving and storing wikidata information from SPARQL...")
    results_by_id = utils.construct_and_run_query(type_qid,
                                                  event_type_matching,
                                                  languages,
                                                  wdt_fn_mappings_COL,
                                                  limit)
    wdt_ids = []
    if not len(results_by_id.items()):
        return [], ''
    for full_wdt_id, inc_data in results_by_id.items():
        extra_info = inc_data['extra_info']
        direct_types = {direct_type.replace('http://www.wikidata.org/entity/', 'wd:')
                        for direct_type in inc_data['direct_types']}
        wdt_id = full_wdt_id.split('/')[-1]
        wdt_ids.append(wdt_id)

        ref_texts = []
        for language, name in inc_data['references'].items():
            ref_text = classes.ReferenceText(
                name=name,
                language=language,
                found_by=['SPARQL']
            )
            ref_texts.append(ref_text)

        incident = classes.Incident(
            incident_type=type_qid,
            wdt_id=wdt_id,
            direct_types=direct_types,
            extra_info=extra_info,
            reference_texts=ref_texts
        )
        incidents.append(incident)

    print("Wikidata querying and storing finished. Number of incidents:", len(incidents))
    ## debugging: store original incidents':
    all_incidents = dict()
    # print(type(incidents), type(type_qid))
    # print(type(incidentcs[5]))
    all_incidents[type_qid] = [inc.wdt_id for inc in incidents]
    with open('json/all_incidents.json', 'w') as outfile:
        json.dump(all_incidents, outfile)
    print('\n### 2. ### Enriching the reference texts through the Wikipedia-Wikidata API...')
    incidents = add_wikipedia_pages_from_api(incidents, wdt_ids)
    print('API querying done. Number of incidents:', len(incidents))
    return incidents


def obtain_reference_texts(incidents, wiki_folder, wiki_uri2path_info, language2info):
    print(
        '\n### 3. ### Retrieve reference text information: text and entity annotations from the local version of Wikipedia.')
    new_incidents = []
    for incident in tqdm(incidents):
        new_reference_texts = []
        for ref_text in incident.reference_texts:
            language = ref_text.language
            wiki_title = ref_text.name

            prefix = language2info[ref_text.language]['prefix']

            text, annotations, success, reason = wu.load_wiki_page_info(wiki_title,
                                                                        prefix,
                                                                        language,
                                                                        wiki_folder,
                                                                        wiki_uri2path_info)

            if success:
                ref_text.annotations = annotations
                ref_text.content = text
                new_reference_texts.append(ref_text)
        new_reference_texts = utils.deduplicate_ref_texts(new_reference_texts)

        if len(
                new_reference_texts):  # if there are reference texts with text, try to get more data by using the Wiki langlinks info we have stored.
            incident.reference_texts = new_reference_texts
            new_incidents.append(incident)
    print('Retrieval of reference texts done. Number of incidents:', len(new_incidents))
    return new_incidents


def get_primary_rt_links(incidents):
    for incident in tqdm(incidents):
        for ref_text in incident.reference_texts:
            ext_links = native_api_utils.obtain_primary_rt_links(ref_text.name, ref_text.language)
            if ext_links:
                ref_text.primary_ref_texts = ext_links
    return incidents


if __name__ == '__main__':
    from docopt import docopt

    start_init = time.time()

    # load arguments
    arguments = docopt(__doc__)
    print()
    print('PROVIDED ARGUMENTS')
    print(arguments)
    print()

    mwep_settings = json.load(open(arguments['--config_path']))
    event_types = {line.strip()
                   for line in open(arguments['--path_event_types'])}
    crawl_wikipedia_sources = arguments['--wikipedia_sources'] == "True"
    max_pilot_incidents = mwep_settings['max_pilot_incidents']
    verbose = int(arguments['--verbose'])

    # settings for crawling Wikipedia sources
    excluded_domains = set(mwep_settings['newsplease']['excluded_domains'])
    accepted_languages = arguments['--languages'].split('-')
    title_required = mwep_settings['newsplease']['title_required']
    range_start, range_end = mwep_settings['newsplease']['num_chars_range']
    num_chars_range = range(int(range_start),
                            int(range_end))
    startswith = mwep_settings['newsplease']['startswith']
    timeout = mwep_settings['newsplease']['timeout']
    illegal_substrings = mwep_settings['newsplease']['illegal_substrings']
    illegal_chars_in_title = mwep_settings['newsplease']['illegal_chars_in_title']

    wiki_folder = mwep_settings['wiki_folder']
    naf_output_folder = mwep_settings['naf_output_folder']
    rdf_folder = mwep_settings['rdf_folder']
    bin_folder = mwep_settings['bin_folder']
    json_folder = mwep_settings['json_folder']

    event_type_matching = mwep_settings['event_type_matching']
    json_wd_to_sem = arguments['--path_mapping_wd_to_sem']

    project = arguments['--project']

    utils.remove_and_create_folder(rdf_folder)
    utils.remove_and_create_folder(naf_output_folder)
    utils.remove_and_create_folder(bin_folder)
    utils.remove_and_create_folder(json_folder)

    print('NAF, RDF, JSON, and BIN directories have been re-created')

    # load index and language info
    path_uri2path_info = os.path.join(wiki_folder, 'page2path.p')
    print(path_uri2path_info)
    with open(path_uri2path_info, 'rb') as infile:
        wiki_uri2path_info = pickle.load(infile)  # make take some time

    language_info_path = os.path.join(wiki_folder, 'language2info.json')
    with open(language_info_path, 'r')  as infile:
        language2info = json.load(infile)

    print("Wikipedia indices loaded")

    wiki_langlinks_path = mwep_settings['wiki_langlinks_path']
    with open(wiki_langlinks_path, 'rb') as infile:
        wiki_langlinks = pickle.load(infile)

    print('Wikipedia parallel titles loaded')

    # load spaCy models
    spacy_models = mwep_settings['spacy_models']
    models = {}
    for model_info in spacy_models.split(';'):
        language, model_name = model_info.split('-')
        models[language] = spacy.load(model_name)

    print("Spacy models have been loaded.")

    end_init = time.time()
    print('Init phase done. Time needed to initialize the extractor', utils.format_time(end_init - start_init), 'sec')

    all_inc_stats = []

    languages = arguments['--languages'].split('-')

    pilot_collections = []

    for incident_type_uri in event_types:

        incident_type = incident_type_uri

        pilot_and_languages = languages + ['pilot']

        inc_stats = [incident_type_uri, ','.join(languages)]

        print('\n\n\n')
        print('----- INCIDENT TYPE: %s -----' % incident_type_uri)
        print('\n\n')

        start = time.time()

        # Query SPARQL and the API to get incidents, their properties, and labels.
        incidents = retrieve_incidents_per_type(incident_type_uri,
                                                event_type_matching,
                                                json_wd_to_sem,
                                                99999)

        if not len(incidents):
            print('NO INCIDENTS FOUND FOR %s. Continuing to next type...')
            continue

        new_incidents = obtain_reference_texts(incidents, wiki_folder, wiki_uri2path_info, language2info)

        collection = classes.IncidentCollection(incidents=new_incidents,
                                                incident_type=incident_type,
                                                incident_type_uri=incident_type_uri,
                                                languages=languages)

        output_file = utils.make_output_filename(bin_folder,
                                                 incident_type_uri,
                                                 languages)

        with open(output_file, 'wb') as of:
            pickle.dump(collection, of)

        inc_stats.append(len(collection.incidents))

        ttl_filename = '%s/%s_%s.ttl' % (rdf_folder, incident_type_uri, '_'.join(languages))
        collection.serialize(ttl_filename)

        after_extraction = time.time()

        pilots = pilot_utils.create_pilot_data(collection,
                                               languages,
                                               mwep_settings['processing']["must_have_all_languages"],
                                               mwep_settings['processing']["must_have_english"],
                                               mwep_settings['processing']["one_page_per_language"])

        if len(pilots) > max_pilot_incidents:
            pilots = list(pilots)[:max_pilot_incidents]
            print(f'selected first {max_pilot_incidents} pilot incidents')

        after_pilot_selection = time.time()

        pilots = get_primary_rt_links(pilots)

        after_primary_texts = time.time()

        pilot_collection = classes.IncidentCollection(incidents=pilots,
                                                      incident_type_uri=incident_type_uri,
                                                      incident_type=incident_type,
                                                      languages=languages)

        pilot_collections.append(pilot_collection)

        ttl_filename = '%s/%s_%s_pilot.ttl' % (rdf_folder, incident_type_uri, '_'.join(pilot_and_languages))
        pilot_collection.serialize(ttl_filename)

        if len(pilot_collection.incidents) == 0:
            print('No pilot incidents for type %s' % incident_type_uri)
        else:
            print('start pilot data processing', datetime.now())

        for incident_obj in pilot_collection.incidents:

            # add primary text urls
            if crawl_wikipedia_sources:
                primary_text_urls = {primary_text_url
                                     for ref_text_obj in incident_obj.reference_texts
                                     for primary_text_url in ref_text_obj.primary_ref_texts}
                print("number of urls to reference texts:", len(primary_text_urls))
                primary_url_to_ref_text_obj = crawl_utils.get_ref_text_obj_of_primary_reference_texts(primary_text_urls,
                                                                                                      timeout,
                                                                                                      startswith=startswith,
                                                                                                      accepted_languages=accepted_languages,
                                                                                                      excluded_domains=excluded_domains,
                                                                                                      title_required=True,
                                                                                                      num_chars_range=num_chars_range,
                                                                                                      illegal_substrings=illegal_substrings,
                                                                                                      illegal_chars_in_title=illegal_chars_in_title,
                                                                                                      verbose=verbose)

                for url, primary_ref_text_obj in primary_url_to_ref_text_obj.items():
                    incident_obj.reference_texts.append(primary_ref_text_obj)

            # process with spaCy
            for ref_text_obj in incident_obj.reference_texts:
                wiki_title = ref_text_obj.name
                language = ref_text_obj.language
                annotations = ref_text_obj.annotations
                text = ref_text_obj.content
                uri = ref_text_obj.uri

                prefix = language2info[language]['prefix']

                # dct of document
                if ref_text_obj.found_by == ['Wikipedia source']:
                    if ref_text_obj.creation_date is not None:
                        dct = ref_text_obj.creation_date
                    else:
                        dct = datetime(1,1,1)
                else: # wikipedia page
                    year, month, day = language2info[language]['year_month_day']
                    dct = datetime(year, month, day)

                print(ref_text_obj.name, ref_text_obj.uri, ref_text_obj.found_by, dct)

                nlp = models[language]

                pilot_utils.text_to_naf(wiki_title,
                                        languages,
                                        text,
                                        uri,
                                        annotations,
                                        prefix,
                                        language,
                                        nlp,
                                        dct,
                                        output_folder=naf_output_folder,
                                        wiki_langlinks=wiki_langlinks)

        out_file = utils.make_output_filename(bin_folder, incident_type_uri, pilot_and_languages)

        with open(out_file, 'wb') as of:
            pickle.dump(pilot_collection, of)

        # add Wikidata information to NAF (entities and coreferences layer)
        xml_utils.add_wikidata_uris_to_naf_files(inc_coll_obj=collection,
                                                 main_naf_folder=mwep_settings['naf_output_folder'],
                                                 languages=accepted_languages,
                                                 verbose=2)

        inc_stats.append(len(pilot_collection.incidents))

        end = time.time()

        inc_stats.append(utils.format_time(after_extraction - start))
        inc_stats.append(utils.format_time(after_pilot_selection - after_extraction))
        inc_stats.append(utils.format_time(after_primary_texts - after_pilot_selection))
        inc_stats.append(utils.format_time(end - after_primary_texts))
        inc_stats.append(utils.format_time(end - start))

        all_inc_stats.append(inc_stats)

    json_utils.create_indices_from_bin(pilot_collections, project, json_folder)

    headers = ['Type', 'Languages', '#incidents', '#pilot incidents', 'Time to extract incidents+RTs',
               'Time to select pilot data', 'Time to get primary RT links',
               'Time to run spacy, enrich, and store to NAF+RDF', 'Total time']

    df = pd.DataFrame(all_inc_stats, columns=headers)
    print(df.to_csv(index=False))

    print('TOTAL TIME TO RUN THE SCRIPT for', event_types, ':', utils.format_time(end - start_init), 'sec')
