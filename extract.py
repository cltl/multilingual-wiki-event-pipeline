import wikipedia
import requests
from pprint import pprint
import pickle

import classes

wikipedia.set_lang("nl")
wdt_sparql_url = 'https://query.wikidata.org/sparql'

incident_type='election'
output_file='bin/%s.bin' % incident_type

def obtain_wiki_text_and_references(title):
    """
    Given a (Dutch) Wikipedia title, obtain its content and list of references.
    """
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

def construct_and_run_query(type_label, limit):
    """
    Construct a wikidata query to obtain all events of a specific type with their structured data, then run this query.
    """

    query = """
    SELECT ?incident ?label ?country ?countryLabel ?time WHERE {
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      ?type_id rdfs:label "%s"@en.
      ?incident wdt:P31 ?type_id;
                rdfs:label ?label;
                wdt:P17 ?country;
                wdt:P585 ?time.
      filter(lang(?label) = 'nl')
    } limit %d
    """ % (type_label, limit)

    r = requests.get(wdt_sparql_url, params = {'format': 'json', 'query': query})
    response = r.json()
    print(response)
    results=response['results']['bindings']
    
    return results

def retrieve_incidents_per_type(type_label, limit=5000):
    """
    Given an event type identifier, retrieve incidents that belong to this type.
    """

    incidents=[]

    query_results=construct_and_run_query(type_label, limit)

    for entry in query_results:
        wdt_id=entry['incident']['value']
        name=entry['label']['value']
        country_id=entry['country']['value']
        country_name=entry['countryLabel']['value']
        time=entry['time']['value']
        incident=classes.Incident(
                incident_type=type_label,
                wdt_id=wdt_id,
                name=name,
                country_id=country_id,
                country_name=country_name,
                time=time
                )
        incidents.append(incident)
    return incidents

if __name__ == '__main__':
    incidents=retrieve_incidents_per_type(incident_type)
    print(len(incidents))
    for incident in incidents:
        content, references=obtain_wiki_text_and_references(incident.name)
        incident.wiki_content=content
        incident.sources=references
        incident.language='nl'
#        pprint(vars(incident))

    with open(output_file, 'wb') as of:
        pickle.dump(incidents, of)
