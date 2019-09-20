import shutil
import os.path
import requests
from collections import defaultdict
import time
from datetime import datetime
import pickle
import networkx as nx
from glob import glob
import os
import classes

wdt_sparql_url = 'https://query.wikidata.org/sparql'

def format_time(t):
    """
    Format time with two decimals.
    """
    return round(t,2)

def make_output_filename(bindir, incident_type, languages):
    """
    Create a filename based on the incident type and languages. 
    """
    output_file='%s/%s_%s.bin' % (bindir, incident_type, ','.join(languages))
    return output_file

def remove_and_create_folder(fldr):
    """
    Remove a folder, if existing, and re-create it.
    """
    if  os.path.exists(fldr):
        shutil.rmtree(fldr)
    os.mkdir(fldr)

def split_in_batches(a_list, batch_size=500):
    """Yield successive n-sized chunks from a_list."""
    for i in range(0, len(a_list), batch_size):
        yield a_list[i:i + batch_size]

def get_results_with_retry(wdt_sparql_url, query):
    """
    Run SPARQL query multiple times until the results are there.
    """
    while True:
        try:
            r = requests.get(wdt_sparql_url,
                     params = {'format': 'json', 'query': query})
        #    res_text=r.text
        #    response = json.loads(res_text)
            response = r.json()
            break
        except Exception as e:
            print(e, 'error, retrying')
            time.sleep(2)
            continue
    return response

def obtain_label(wd_id):
    """
    Obtain an English label for a property of Wikidata.
    """
    query = """
    SELECT ?label WHERE {
    wd:%s rdfs:label ?label . 
    FILTER(LANG(?label) = "" || LANGMATCHES(LANG(?label), "en"))
    }
    LIMIT 1
    """ % wd_id

    response=get_results_with_retry(wdt_sparql_url, query) 

    results=response['results']['bindings']
    if not len(results):
        return ''
    the_label=results[0]['label']['value']
    return the_label

def construct_and_run_query(type_label, languages, more_props, limit):
    """
    Construct a wikidata query to obtain all events of a specific type with their structured data, then run this query.
    """
    
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
    opt_var_labels=[]
    optional_more_info=""
    for fn_role, wdt_prop_paths in more_props.items():
        for a_path in wdt_prop_paths:
            var='?' + a_path.replace('wdt:', '').replace('/', '_')       # fn_role.split('@')[-1]
            if var not in opt_vars:
                label_var=f"{var}Label"
                clause=f"""OPTIONAL {{ \n\t?incident {a_path} {var} }}\n\t"""
                optional_more_info+=clause
                opt_vars.append(var)
                if type_label not in {"election"}:
                    opt_var_labels.append(var + 'Label')

    query = """
    SELECT DISTINCT ?type_id ?direct_type ?incident ?incidentLabel %s %s %s WHERE {
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      ?type_id rdfs:label "%s"@en .
      ?incident wdt:P31*/wdt:P279* ?type_id ;
                wdt:P31 ?direct_type .
      %s
      %s
    } limit %d
    """ % (return_langs, ' '.join(opt_vars), ' '.join(opt_var_labels), type_label, optional_clauses_str, optional_more_info, limit)

    print('QUERY:\n', query)

    response=get_results_with_retry(wdt_sparql_url, query)

    results=response['results']['bindings']

    results_by_id=index_results_by_id(results, lang2var, more_props)
   
    return results_by_id


def index_results_by_id(raw_results, lang2var, extra_info):
    """
    Aggregate/index the SPARQL results by incident ID.
    """
    indexed_results=defaultdict(dict)
    for entry in raw_results:
        wdt_id=entry['incident']['value']
        current_result=indexed_results[wdt_id]
        if not len(current_result.keys()):
            current_result=defaultdict(dict)

        if 'references' not in current_result:
            current_result['references']=defaultdict(str)
        name=entry['incidentLabel']['value']
        current_result['type_id']=entry['type_id']['value']

        if 'direct_types' not in current_result.keys():
            current_result['direct_types']=set()
        current_result['direct_types'].add(entry['direct_type']['value'])

        for l, var in lang2var.items():
            label_in_lang=var.strip('?')
            if label_in_lang in entry.keys():
                name_in_lang=entry[label_in_lang]['value']
                current_result['references'][l]=name_in_lang

        if 'extra_info' not in current_result.keys():
            current_result['extra_info']=defaultdict(set)
        for predicate, wdt_prop_paths in extra_info.items():
            for a_path in wdt_prop_paths:
                var=a_path.replace('wdt:', '').replace('/', '_')       # fn_role.split('@')[-1] 
                if var in entry.keys() and entry[var]['value']:
                    if var + 'Label' in entry.keys() and entry[var + 'Label']['value']:
                        complex_value='%s | %s' % (entry[var]['value'], entry[var + 'Label']['value'])
                    else:
                        complex_value=entry[var]['value']
                    current_result['extra_info'][predicate].add(complex_value)
        indexed_results[wdt_id]=current_result
    return indexed_results

def get_languages_and_names(ref_texts):
    """Obtain list of languages and names in our reference texts."""
    found_names=[]
    found_languages=[]
    for ref_text in ref_texts:
        found_languages.append(ref_text.language)
        found_names.append(ref_text.name)
    return found_languages, found_names

def deduplicate_ref_texts(ref_texts):
    """Deduplicate reference texts by removing those that have the same content."""
    new_ref_texts=[]
    for rt in ref_texts:
        to_keep=True
        for other_rt in ref_texts:
            if rt.language==other_rt.language and rt.name<other_rt.name:
                if rt.content==other_rt.content:
                    to_keep=False
                    break
        if to_keep:
            new_ref_texts.append(rt)
    return new_ref_texts


def extract_subclass_of_ontology(wdt_sparql_url,
                                 output_folder,
                                 output_basename,
                                 verbose=0):
    """
    determine whether event type one is subclass or instance of event type two

    SELECT ?subclass1 ?subclass2 WHERE {
      ?subclass1 wdt:P279 ?subclass2 .
    }

    :rtype: set
    :return: set of relations, i.e., x is subclass of y
    """
    query = """SELECT ?subclass1 ?subclass2 WHERE {
      ?subclass1 wdt:P279 ?subclass2 .
    }"""
    output_path = os.path.join(output_folder, output_basename)

    if os.path.exists(output_path):
        set_of_relations = pickle.load(open(output_path, 'rb'))
        if verbose >= 2:
            print('loaded subclass of relations from cache')
    else:
        if verbose >= 2:
            print('extracting subclass of relations from api')
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        os.mkdir(output_folder)

        if verbose >= 2:
            print(f'start {datetime.now()}')
            print(query)

        response = get_results_with_retry(wdt_sparql_url, query)

        set_of_relations = set()
        for info in response['results']['bindings']:
            x = info['subclass1']['value']
            y = info['subclass2']['value']
            set_of_relations.add((x,y))

        if verbose >= 2:
            print(f'found {len(set_of_relations)} unique relations')
            print(f'end {datetime.now()}')

        with open(output_path, 'wb') as outfile:
            pickle.dump(set_of_relations, outfile)

    return set_of_relations


def load_ontology_as_directed_graph(input_path, output_path, verbose=0):
    """

    :param str input_path: output of function extract_subclass_of_ontology

    :rtype: networkx.classes.digraph.DiGraph
    :return: directed graph containing all subclass of relations of Wikidata
    """
    with open(input_path, 'rb') as infile:
        set_of_relations = pickle.load(infile)

    if os.path.exists(output_path):
        g = nx.read_gpickle(output_path)
        return g

    relations = []
    for x, y in set_of_relations:  # x is subclass of y
        x_short = x.replace('http://www.wikidata.org/entity/', 'wd:')
        y_short = y.replace('http://www.wikidata.org/entity/', 'wd:')
        relations.append((y_short, x_short))

    g = nx.DiGraph()
    g.add_edges_from(relations)

    the_ancestors = nx.ancestors(g, 'wd:Q1656682')

    roots = []
    for the_ancestor in the_ancestors:
        children = nx.ancestors(g, the_ancestor)
        if not children:
            roots.append(the_ancestor)

    assert len(roots) == 1, f'multiple roots found {roots}'
    root = roots[0]

    event_node = 'wd:Q1656682'
    shortest_path_to_event = nx.shortest_path(g, root, event_node)

    all_event_subclasses = nx.descendants(g, event_node)
    if verbose >= 2:
        print(f'loaded graph with {len(g.edges())} edges')
        print(f'found {len(all_event_subclasses)} events under the event node in Wikidata')
        print(f'root: {root}')
        print(f'shortest path from event node to root node: {shortest_path_to_event}')
        print(nx.info(g))

    nx.write_gpickle(g, output_path)

    return g


def update_incident(instance_of_values, g, verbose=0):
    """
    get all items from direct instance of values to event node
    ('wd:Q1656682')

    :param set instance_of_values: instance of values, i.e.,
    wd:IDENTIFIER
    :param networkx.classes.digraph.DiGrap g: directed graph
    """
    all_ancestors = set()
    for instance_of_value in instance_of_values:
        assert instance_of_value.startswith('wd:')
        for items in nx.all_simple_paths(g, 'wd:Q1656682', instance_of_value):
            all_ancestors.update(items)
    return all_ancestors


def load_event_type2instancefreq(wdt_sparql_url, output_path, verbose=0):
    """

    :param str wdt_sparql_url:
    :return:
    """

    query = """SELECT DISTINCT ?type_id (count(?incident) as ?num) WHERE {
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        ?type_id wdt:P279* wd:Q1656682 .
        ?incident wdt:P31 ?type_id .
        ?incident rdfs:label ?label .
        FILTER (langMatches( lang(?label), "EN" ) )
        } group by ?type_id
        order by desc(?num)
    """

    if verbose >= 2:
        print(f'start {datetime.now()}')
        print(query)

    response = get_results_with_retry(wdt_sparql_url, query)

    event_type2instance_freq = dict()
    for info in response['results']['bindings']:
        event_type = info['type_id']['value']
        event_type_short = event_type.replace('http://www.wikidata.org/entity/', 'wd:')
        freq = int(info['num']['value'])
        event_type2instance_freq[event_type_short] = freq

    if verbose >= 2:
        print(f'found {len(event_type2instance_freq)} unique relations')
        print(f'min and max: {min(event_type2instance_freq.values())} {max(event_type2instance_freq.values())}')
        print(f'end {datetime.now()}')

    with open(output_path, 'wb') as outfile:
        pickle.dump(event_type2instance_freq, outfile)

    return event_type2instance_freq


def merge_incident_collections(paths_incident_collections,
                               config,
                               incident_type,
                               incident_type_uri,
                               g,
                               verbose=0):
    """
    merge incident collections

    :param iterable paths_incident_collections: iterable of paths where IncidentCollection objects are stored
    :param module config: the module config.py (in the same directory)
    :param str incident_type: event type, e.g., 'event'
    :param str incident_type_uri: uri of incident type, e.g., https://www.wikidata.org/wiki/Q1656682
    :param g: directed graph containing subclass of directed graph from Wikidata

    :rtype: IncidentCollection
    :return: instance of IncidentCollection
    """
    # create new IncidentCollection object
    merged_inc_coll_obj = classes.IncidentCollection(incident_type=incident_type,
                                                     incident_type_uri=incident_type_uri,
                                                     languages=[])

    for inc_coll_obj_path in paths_incident_collections:
    
        with open(inc_coll_obj_path, 'rb') as infile:
            inc_coll_obj = pickle.load(infile)

        # merge languages
        for language in inc_coll_obj.languages:
            if language not in merged_inc_coll_obj.languages:
                merged_inc_coll_obj.languages.append(language)

        # merge incidents
        to_add = True 

        inc_ids_added = set()
        for incident_obj in inc_coll_obj.incidents:
            if incident_obj.wdt_id in inc_ids_added:
                to_add = False
                if verbose >= 2:
                    print(f'found {incident_obj.wdt_id} in more than one incident collection')
    
            found_langs = {ref_text_obj.language
                           for ref_text_obj in incident_obj.reference_texts}
            
            if all([config.must_have_english,
                    'en' not in found_langs]):
                to_add = False

            if all([config.must_have_all_languages,
                    set(config.languages_list) - found_langs]):
                to_add = False
            
        if to_add:
            merged_inc_coll_obj.incidents.append(incident_obj)
            inc_ids_added.add(incident_obj.wdt_id)

        # update subclass of information
        merged_inc_coll_obj.update_incidents_with_subclass_of_info(g, top_node='wd:Q1656682', verbose=verbose)
        merged_inc_coll_obj.event_type2wdt_ids = merged_inc_coll_obj.get_index_event_type2wdt_ids()

    if verbose >= 1:
        print(f'New IncidentCollection object contains information:')
        print(f'about {len(merged_inc_coll_obj.languages)} languages')
        print(f'about {len(merged_inc_coll_obj.incidents)} incidents')
        print(f'about {len(merged_inc_coll_obj.event_type2wdt_ids)} different event types')

    return merged_inc_coll_obj

def get_bin_paths(folder, suffix, pilot=False):
    """
    return iterable of paths with the specified requirements

    :param str folder: folder with *bin files (instances of class IncidentCollection
    :param str suffix: path suffixs
    :param bool pilot: True -> return only files co

    :rtype: list
    :return: list of paths
    """
    paths = []

    for path in glob(f'{folder}/*{suffix}'):

        basename = os.path.basename(path)
        if pilot:
            if 'pilot' not in basename:
                continue
        else:
            if 'pilot' in basename:
                continue

        paths.append(path)

    return paths
