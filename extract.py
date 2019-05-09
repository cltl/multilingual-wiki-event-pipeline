from pprint import pprint
import pickle
from tqdm import tqdm
import json
from collections import defaultdict

import native_api_utils
import classes
import config
import utils

incident_types=config.incident_types
languages_list=config.languages_list

def get_additional_reference_texts(ref_texts, found_names, found_languages):
    """
    Get more reference texts using the langlinks of the other API.
    """
    search_for_languages=set(languages)-set(found_languages)
    if not search_for_languages:
        return ref_texts

    to_query=defaultdict(set)
    for ref_text in ref_texts:
        langlinks=ref_text.langlinks
        for useful_lang in search_for_languages&set(langlinks.keys()):
            to_query[useful_lang].add(langlinks[useful_lang])

    props=['extracts', 'langlinks', 'extlinks']
    for language, pages in to_query.items():
        for page in pages:
            page_info=native_api_utils.obtain_wiki_page_info(page, language, props)
            if 'extract' in page_info.keys():
                ref_text = classes.ReferenceText(
                    wiki_content=page_info['extract'],
                    langlinks=page_info['langlinks'],
                    name=page,
                    language=language,
                    found_by=['langlinks']
                )
                if 'extlinks' in page_info.keys():
                    ref_text.sources=page_info['extlinks']
                ref_texts.append(ref_text)
    return ref_texts

def add_wikipedia_pages_from_api(incidents, wdt_ids, raw_results):

    id_batches=utils.split_in_batches(wdt_ids, 50)

    for index, batch in enumerate(id_batches):
        print('Querying batch number %d' % index)
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

def retrieve_incidents_per_type(type_label, limit=10):
    """
    Given an event type identifier, retrieve incidents that belong to this type.
    """

    with open('wdt_fn_mappings/change_of_leadership.json', 'rb') as f:
        wdt_fn_mappings_COL=json.load(f)

    incidents=[]
    print("Retrieving and storing wikidata information...")
    results_by_id=utils.construct_and_run_query(type_label, languages, wdt_fn_mappings_COL, limit)  
    print("Wikidata querying and storing finished. Number of incidents:")
    print(len(results_by_id.keys()))
    wdt_ids=[]
    for full_wdt_id, inc_data in results_by_id.items():
        extra_info=inc_data['extra_info']
            
        wdt_id=full_wdt_id.split('/')[-1]
        wdt_ids.append(wdt_id)

        ref_texts=[]
        for language, name in inc_data['references'].items():
            print(language, name, wdt_id)
            ref_text=classes.ReferenceText(
                        name=name,
                        language=language,
                        found_by=['SPARQL']
                    )
            ref_texts.append(ref_text)

        incident=classes.Incident(
                incident_type=type_label,
                wdt_id=wdt_id,
                extra_info=extra_info,
                reference_texts=ref_texts
            )
        incidents.append(incident)
    print('Now looking into wikipedia...')
    incidents=add_wikipedia_pages_from_api(incidents, wdt_ids, results_by_id)
    print('Wikipedia querying done')
    return incidents

if __name__ == '__main__':

    for incident_type in incident_types:
        for languages in languages_list:
            incidents=retrieve_incidents_per_type(incident_type, 3000)
            print(len(incidents))
            new_incidents=[]
            for incident in tqdm(incidents):
                new_reference_texts=[]
                found_names=[]
                found_languages=[]
                for ref_text in incident.reference_texts:
                    props=['extracts', 'langlinks', 'extlinks']
                    page_info=native_api_utils.obtain_wiki_page_info(ref_text.name, ref_text.language, props, other_languages=set(languages)-set(ref_text.language))
                    if 'extract' in page_info.keys():
                        ref_text.wiki_content=page_info['extract']
                        if 'extlinks' in page_info.keys():
                            ref_text.sources=page_info['extlinks']
                        ref_text.langlinks=page_info['langlinks']
                        #ref_text.wiki_uri=uri
                        new_reference_texts.append(ref_text)
                        found_languages.append(ref_text.language)
                        found_names.append(ref_text.name)
                if len(new_reference_texts):
                    all_ref_texts=defaultdict(list)
                    new_reference_texts=get_additional_reference_texts(new_reference_texts, found_names, found_languages)
                    #for r in new_reference_texts:
                    #    all_ref_texts[r.language].append(r.name)
                    incident.reference_texts=new_reference_texts
                    new_incidents.append(incident)

            collection=classes.IncidentCollection(incidents=new_incidents,
                                     incident_type=incident_type,
                                     languages=languages)
            
            output_file=utils.make_output_filename(incident_type, languages)
            
            with open(output_file, 'wb') as of:
                pickle.dump(collection, of)
