import wikipedia
import wikipediaapi
from pprint import pprint
import pickle
from tqdm import tqdm

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

    wiki = wikipediaapi.Wikipedia(found_languages[0])
    page = wiki.page(found_names[0])
    if not page.exists():
        if len(found_languages)<2: 
            return ref_texts
        wiki = wikipediaapi.Wikipedia(found_languages[1])
        page = wiki.page(found_names[1])
        if not page.exists():
            return ref_texts
    try:    
        p_langs = page.langlinks
    except KeyError:
        return ref_texts
    for lang in search_for_languages:
        if lang in p_langs:
            p_lang=p_langs[lang]
            p_lang_uri=p_lang.fullurl
            p_lang_content=p_lang.text
            p_lang_title=p_lang.title
            
            ref_text = classes.ReferenceText(
                        name=p_lang_title,
                        language=lang,
                        wiki_uri=p_lang_uri,
                        wiki_content=p_lang_content,
                        sources=[]
                    )
            ref_texts.append(ref_text)
    return ref_texts

def obtain_wiki_text_and_references(title, lang):
    """
    Given a Wikipedia title in some language, obtain its content and list of references.
    """
    wikipedia.set_lang(lang)
    try:
        wp=wikipedia.page(title)
    except:
        return '', [], ''
    try:
        refs=wp.references
    except:
        refs=[]
    try:
        content=wp.content
    except:
        content=''
    try:
        wiki_url=wp.url
    except:
        wiki_url=''
    return content, refs, wiki_url

def retrieve_incidents_per_type(type_label, limit=10):
    """
    Given an event type identifier, retrieve incidents that belong to this type.
    """

    incidents=[]

    results_by_id=utils.construct_and_run_query(type_label, languages, limit)    
    print(len(results_by_id.keys()))
    for wdt_id, inc_data in results_by_id.items():
        country_id=inc_data['country']
        country_name=inc_data['countryLabel']
        time=inc_data['time']
        ref_texts=[]
        for language, name in inc_data['references'].items():
            print(language, name, wdt_id)
            ref_text=classes.ReferenceText(
                        name=name,
                        language=language
                    )
            ref_texts.append(ref_text)
            
        incident=classes.Incident(
                incident_type=type_label,
                wdt_id=wdt_id,
                country_id=country_id,
                country_name=country_name,
                time=time,
                reference_texts=ref_texts
            )
        incidents.append(incident)
    return incidents

if __name__ == '__main__':

    for incident_type in incident_types:
        for languages in languages_list:

            incidents=retrieve_incidents_per_type(incident_type, 50000)
            print(len(incidents))
            new_incidents=[]
            for incident in tqdm(incidents):
                new_reference_texts=[]
                found_names=[]
                found_languages=[]
                for ref_text in incident.reference_texts:
                    content, references, uri=obtain_wiki_text_and_references(ref_text.name, ref_text.language)
                    if content:
                        ref_text.wiki_content=content
                        ref_text.sources=references
                        ref_text.wiki_uri=uri
                        new_reference_texts.append(ref_text)
                        found_languages.append(ref_text.language)
                        found_names.append(ref_text.name)
                if len(new_reference_texts):
                    new_reference_texts=get_additional_reference_texts(new_reference_texts, found_names, found_languages)
                    incident.reference_texts=new_reference_texts
                    new_incidents.append(incident)

            collection=classes.IncidentCollection(incidents=new_incidents,
                                     incident_type=incident_type,
                                     languages=languages)
            
            output_file=utils.make_output_filename(incident_type, languages)
            
            with open(output_file, 'wb') as of:
                pickle.dump(collection, of)
