import json
import requests
import sys
from collections import defaultdict

wdt_sparql_url = 'https://query.wikidata.org/sparql'

def make_output_filename(incident_type, languages):
    """
    Create a filename based on the incident type and languages. 
    """
    output_file='bin/%s_%s.bin' % (incident_type, ','.join(languages))
    return output_file

def split_in_batches(a_list, batch_size=500):
    """Yield successive n-sized chunks from a_list."""
    for i in range(0, len(a_list), batch_size):
        yield a_list[i:i + batch_size]

def prepare_list_for_sparql(x):
    return '("' +  '", "'.join(x) + '")'

def construct_and_run_query(type_label, languages, more_props, limit):
    """
    Construct a wikidata query to obtain all events of a specific type with their structured data, then run this query.
    """

    #langs=prepare_list_for_sparql(languages)
    
    lang2var={}
    for l in languages:
        var='?label_%s' % l
        lang2var[l]=var
    return_langs=' '.join(lang2var.values())
    
    optional_clauses_str=""
    for l, var in lang2var.items():
        clause=f"""OPTIONAL {{ \n\t?incident rdfs:label {var}.\n\tFILTER ( LANGMATCHES ( LANG ( {var} ), \"{l}\" )) }}\n\t"""
        optional_clauses_str+=clause

    opt_vars=[]
    optional_more_info=""
    for fn_role, wdt_prop_paths in more_props.items():
        var='?' + fn_role.split('@')[-1]
        for a_path in wdt_prop_paths:
            clause=f"""OPTIONAL {{ \n\t?incident {a_path} {var} }}\n\t"""
            optional_more_info+=clause
        opt_vars.append(var)

    query = """
    SELECT DISTINCT ?incident ?incidentLabel ?country ?countryLabel ?time %s %s WHERE {
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      ?type_id rdfs:label "%s"@en.
      ?incident wdt:P31*/wdt:P279* ?type_id;
                wdt:P17 ?country;
                wdt:P585 ?time.
      %s
      %s
    } limit %d
    """ % (return_langs, ' '.join(opt_vars), type_label, optional_clauses_str, optional_more_info, limit)

    print(query)
    sys.exit()

    r = requests.get(wdt_sparql_url, 
                     params = {'format': 'json', 'query': query})
    response = json.loads(r.text)
    
    results=response['results']['bindings']

    results_by_id=index_results_by_id(results, lang2var)
   
    return results_by_id


def index_results_by_id(raw_results, lang2var):
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

        for l, var in lang2var.items():
            label_in_lang=var.strip('?')
            if label_in_lang in entry.keys():
                name_in_lang=entry[label_in_lang]['value']
                current_result['references'][l]=name_in_lang
        
#        language=entry['lang']['value']
#        current_result['references'][language]=name
    return indexed_results
