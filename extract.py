import wikipedia
from pprint import pprint
import pickle

import classes
import config
import utils

incident_types=config.incident_types
languages_list=config.languages_list

def obtain_wiki_text_and_references(title, lang):
    """
    Given a Wikipedia title in some language, obtain its content and list of references.
    """
    wikipedia.set_lang(lang)
    try:
        wp=wikipedia.page(title)
    except:
        return '', []
    try:
        refs=wp.references
    except:
        refs=[]
    try:
        content=wp.content
    except:
        content=''
    return content, refs

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
    incidents=retrieve_incidents_per_type(incident_type, 50000)
    print(len(incidents))
    for incident in incidents:
        for ref_text in incident.reference_texts:
            
            content, references=obtain_wiki_text_and_references(ref_text.name, ref_text.language)
            ref_text.wiki_content=content
            ref_text.sources=references
    #        pprint(vars(incident))

    collection=classes.IncidentCollection(incidents=incidents,
                             incident_type=incident_type,
                             languages=languages)
    
    output_file=utils.make_output_filename(incident_type, languages)
    
    with open(output_file, 'wb') as of:
        pickle.dump(collection, of)
