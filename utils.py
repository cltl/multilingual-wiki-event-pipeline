import requests
from collections import defaultdict

wdt_sparql_url = 'https://query.wikidata.org/sparql'

def make_output_filename(incident_type, languages):
    """
    Create a filename based on the incident type and languages. 
    """
    output_file='bin/%s_%s.bin' % (incident_type, ','.join(languages))
    return output_file

def prepare_list_for_sparql(x):
    return '("' +  '", "'.join(x) + '")'

def construct_and_run_query(type_label, limit):
    """
    Construct a wikidata query to obtain all events of a specific type with their structured data, then run this query.
    """

    #langs=prepare_list_for_sparql(languages)
    
    query = """
    SELECT ?incident ?incidentLabel ?country ?countryLabel ?time (lang(?label) as ?lang) WHERE {
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      ?type_id rdfs:label "%s"@en.
      ?incident wdt:P31*/wdt:P279* ?type_id;
                wdt:P17 ?country;
                wdt:P585 ?time.
    } limit %d
    """ % (type_label, limit)

    r = requests.get(wdt_sparql_url, 
                     params = {'format': 'json', 'query': query})
    response = r.json()
    print(response)
    results=response['results']['bindings']
    
    results_by_id=index_results_by_id(results)
    
    return results_by_id


def index_results_by_id(raw_results):
    """
    Aggregate/index the SPARQL results by incident ID.
    """
    indexed_results=defaultdict(dict)
    for entry in raw_results:
        wdt_id=entry['incident']['value']
        current_result=indexed_results[wdt_id]
        current_result['country']=entry['country']['value']
        current_result['countryLabel']=entry['countryLabel']['value']
        current_result['time']=entry['time']['value']
        
        if 'references' not in current_result:
            current_result['references']=defaultdict(str)
        name=entry['incidentLabel']['value']
#        language=entry['lang']['value']
#        current_result['references'][language]=name
    return indexed_results
