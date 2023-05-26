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

for_encoding = 'é'
wdt_sparql_url = 'https://query.wikidata.org/sparql'
WIKIDATA_PREFIX = 'http://www.wikidata.org/entity/'

def format_time(t):
    """
    Format time with two decimals.
    """
    return round(t,2)

def make_output_filename(bindir, incident_type, languages):
    """
    Create a filename based on the incident type and languages. 
    """
    output_file='%s/%s_%s.bin' % (bindir, incident_type, ','.join(sorted(languages)))
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

def construct_and_run_query(type_qid,
                            event_type_matching,
                            languages,
                            more_props,
                            limit):
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
                if type_qid not in {"Q40231"}:
                    opt_var_labels.append(var + 'Label')

    
    if event_type_matching == 'direct_match':
        main_part = f'?incident wdt:P31 wd:{type_qid} .\nBIND(wd:{type_qid} as ?direct_type) .'
    elif event_type_matching == 'subsumed_by':
        main_part = f'?incident wdt:P31*/wdt:P279* wd:{type_qid} ;\nwdt:P31 ?direct_type .'

    query = """
    SELECT DISTINCT ?direct_type ?incident ?incidentLabel %s %s %s WHERE {
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      %s
      %s
      %s
    } limit %d
    """ % (return_langs,
           ' '.join(opt_vars),
           ' '.join(opt_var_labels),
           main_part,
           optional_clauses_str,
           optional_more_info,
           limit)

    print('QUERY:\n', query)

    response=get_results_with_retry(wdt_sparql_url, query)
    
    results=response['results']['bindings']

    results_by_id=index_results_by_id(results, lang2var, more_props)
   
    return results_by_id


#@TODO:
# - create a query to look for a participant in an event of a certain type
# - create a fake instance ID by combining the q-code of the person with the q-code of the event-type
#defaultView:ImageGrid
# SELECT ?person ?prop ?disease
# WHERE
# {
# ?person ?prop ?disease .
# ?person wdt:P31 wd:Q5 .
#       ?disease wdt:P31 wd:Q18123741  #infectious disease
# SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }
# }

# {
#   "head" : {
#     "vars" : [ "person", "prop", "disease" ]
#   },
#   "results" : {
#     "bindings" : [ {
#       "disease" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/entity/Q2840"
#       },
#       "person" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/entity/Q720370"
#       },
#       "prop" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/prop/direct/P509"
#       }
#     }, {
#       "disease" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/entity/Q2840"
#       },
#       "person" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/entity/Q724677"
#       },
#       "prop" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/prop/direct/P509"
#       }
#     }
#   }
# }
def construct_and_run_participant_query(participant_id, type_qid,
                            event_type_matching,
                            languages,
                            more_props,
                            limit):
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
        clause=f"""OPTIONAL {{ \n\t?event rdfs:label {var}.\n\tFILTER ( LANGMATCHES ( LANG ( {var} ), \"{l}\" )) }}\n\t"""
        clause+=f"""OPTIONAL {{ \n\t?participant rdfs:label {var}.\n\tFILTER ( LANGMATCHES ( LANG ( {var} ), \"{l}\" )) }}\n\t"""
        optional_clauses_str+=clause

    opt_vars=[]
    opt_var_labels=[]
    optional_more_info=""
    for fn_role, wdt_prop_paths in more_props.items():
        for a_path in wdt_prop_paths:
            var='?' + a_path.replace('wdt:', '').replace('/', '_')       # fn_role.split('@')[-1]
            if var not in opt_vars:
                label_var=f"{var}Label"
                clause=f"""OPTIONAL {{ \n\t?event {a_path} {var} }}\n\t"""
                optional_more_info+=clause
                opt_vars.append(var)
                if type_qid not in {"Q40231"}:
                    opt_var_labels.append(var + 'Label')

    #### Only works for persons
    if event_type_matching == 'direct_match':
        main_part = f'?participant ?prop ?event . \n ?event wdt:P31 wd:{type_qid} ; \nBIND(wd:{type_qid} as ?direct_type) . \n?participant wdt:P31 wd:{participant_id} .'
        #main_part = f'?incident wdt:P31 wd:{type_qid} .\nBIND(wd:{type_qid} as ?direct_type) .'
    elif event_type_matching == 'subsumed_by':
        main_part = f'?participant ?prop ?event .\n?participant wdt:P31 wd:{participant_id} .\n ?event wdt:P31*/wdt:P279* wd:{type_qid} ;\nwdt:P31 ?direct_type .'
        #main_part = f'?incident wdt:P31*/wdt:P279* wd:{type_qid} ;\nwdt:P31 ?direct_type .'

    query = """
    SELECT DISTINCT ?direct_type ?event ?participant ?participantLabel ?eventLabel %s %s %s WHERE {
      SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
      %s
      %s
    } limit %d
    """ % (return_langs,
           ' '.join(opt_vars),
           ' '.join(opt_var_labels),
           main_part,
           optional_clauses_str,
           #optional_more_info,
           limit)

    print('QUERY:\n', query)

    response=get_results_with_retry(wdt_sparql_url, query)

    results=response['results']['bindings']

    results_by_id=index_results_by_participant_id(results, lang2var, more_props)
    print("HERE ARE THE RESULTS BY ID", results_by_id)
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
        #current_result['type_id']=entry['type_id']['value']

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

#@TODO: adapt this function to handle the results for the participant query
#   "results" : {
#     "bindings" : [ {
#       "event" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/entity/Q2840"
#       },
#       "participant" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/entity/Q720370"
#       },
#       "prop" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/prop/direct/P509"
#       }
#     }, {
#       "event" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/entity/Q2840"
#       },
#       "participant" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/entity/Q724677"
#       },
#       "prop" : {
#         "type" : "uri",
#         "value" : "http://www.wikidata.org/prop/direct/P509"
#       }
#     }
#   }
def index_results_by_participant_id(raw_results, lang2var, extra_info):
    """
    Aggregate/index the SPARQL results by incident ID.
    """
    indexed_results=defaultdict(dict)
    for entry in raw_results:
        participant_id=entry['participant']['value']
        event_id = entry['event']['value']
        wdt_id=event_id+"_"+participant_id
        current_result=indexed_results[wdt_id]
        if not len(current_result.keys()):
            current_result=defaultdict(dict)

        if 'references' not in current_result:
            current_result['references']=defaultdict(str)
        name=entry['eventLabel']['value']
        #current_result['type_id']=entry['type_id']['value']

        if 'direct_types' not in current_result.keys():
            current_result['direct_types']=set()
        current_result['direct_types'].add(entry['event']['value'])

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
        nodes = set()
        for info in response['results']['bindings']:
            x = info['subclass1']['value']
            y = info['subclass2']['value']
            set_of_relations.add((x,y))
            nodes.update([x, y])

        if verbose >= 2:
            print(f'found {len(nodes)} unique nodes')
            print(f'found {len(set_of_relations)} unique relations')
            print(f'end {datetime.now()}')

        with open(output_path, 'wb') as outfile:
            pickle.dump(set_of_relations, outfile)

    return set_of_relations

def all_english_labels_of_descendants_of_topnode(topnode, verbose=0):
    """

    :param str topnode: e.g., "wd:Q1656682"
    :return:
    """
    query = """SELECT DISTINCT ?type_id ?label WHERE {
            SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
            ?type_id wdt:P279* %s .
            ?type_id rdfs:label ?label .
            FILTER (langMatches( lang(?label), "EN" ) )
            }
        """ % topnode

    wdt_id2label_en = {}

    if verbose >= 2:
        print(f'start {datetime.now()}')
        print(query)

    response = get_results_with_retry(wdt_sparql_url, query)

    for info in response['results']['bindings']:
        label_en = info['label']['value']
        full_wdtid = info['type_id']['value']
        wdtid = full_wdtid.replace('http://www.wikidata.org/entity/', 'wd:')
        wdt_id2label_en[wdtid] = label_en

    if verbose >= 2:
        print()
        print(f'found {len(wdt_id2label_en)} Wikidata items with English label for topnode {topnode}')

    return wdt_id2label_en

def load_ontology_as_directed_graph(output_folder, top_node, verbose=0):
    """

    :param str output_folder: folder where all information will be stored
    :param str top_node: top node to use in graph, e.g., 'wd:Q1656682'

    :rtype: networkx.classes.digraph.DiGraph
    :return: directed graph containing all subclass of relations of Wikidata
    """
    graph_path = f'{output_folder}/g.p'
    if os.path.exists(graph_path):
        sub_g = nx.read_gpickle(graph_path)
        return sub_g

    set_of_relations = extract_subclass_of_ontology(wdt_sparql_url,
                                                    output_folder,
                                                    'relations.p',
                                                    verbose=verbose)

    event_type2instance_freq = load_event_type2instancefreq(wdt_sparql_url,
                                                            f'{output_folder}/eventtype2instance_freq.p',
                                                            verbose=verbose)

    event_type2label = all_english_labels_of_descendants_of_topnode(top_node, verbose=verbose)

    relations = []
    for x, y in set_of_relations:  # x is subclass of y
        x_short = x.replace('http://www.wikidata.org/entity/', 'wd:')
        y_short = y.replace('http://www.wikidata.org/entity/', 'wd:')

        if all([x_short in event_type2label,
                y_short in event_type2label]):
                relations.append((y_short, x_short))

    g = nx.DiGraph()
    g.add_edges_from(relations)

    the_descendants = nx.descendants(g, top_node)
    the_descendants.add(top_node)
    sub_g = g.subgraph(the_descendants).copy()

    node_attrs = {}
    for node in sub_g.nodes():
        label = event_type2label[node]
        freq = event_type2instance_freq.get(node, 0)

        info = {
            'label' : label,
            'occurrence_frequency' : freq,
            'features' : [],
            'num_features' : []
        }
        node_attrs[node] = info

    nx.set_node_attributes(sub_g, node_attrs)

    if verbose >= 2:
        print(f'loaded graph with {len(sub_g.edges())} edges')
        print(nx.info(sub_g))
        print('top node information', sub_g.nodes[top_node])

    nx.write_gpickle(sub_g, graph_path)

    return sub_g


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


def get_uris(inc_coll_obj,
             prefix=WIKIDATA_PREFIX,
             rels_to_ignore={'sem:hasTimeStamp'},
             verbose=0):
    """

    :param inc_coll_obj:
    :return:
    """

    short_rel_to_full = {
        'incident' : 'http://semanticweb.cs.vu.nl/2009/11/sem/Event',
        'sem:hasPlace' : 'http://semanticweb.cs.vu.nl/2009/11/sem/hasPlace',
        'sem:hasActor' : 'http://semanticweb.cs.vu.nl/2009/11/sem/hasActor'
    }

    uri_to_rels = defaultdict(set)
    inc_id_to_wd_uris = defaultdict(set)

    for inc_obj in inc_coll_obj.incidents:

        uri_to_rels[inc_obj.wdt_id].add(short_rel_to_full['incident'])
        wd_inc_uri = f'{WIKIDATA_PREFIX}{inc_obj.wdt_id}'
        inc_id_to_wd_uris[wd_inc_uri].add(wd_inc_uri)

        for rel, set_with_uri_and_label in inc_obj.extra_info.items():

            if rel in rels_to_ignore:
                continue

            for uri_and_label in set_with_uri_and_label:
                uri, label = uri_and_label.split(' | ')
                if prefix:
                    if not uri.startswith(prefix):
                        continue

                if prefix:
                    uri = uri.replace(prefix, '')

                uri_to_rels[uri].add(short_rel_to_full[rel])
                inc_id_to_wd_uris[wd_inc_uri].add(f'{WIKIDATA_PREFIX}{uri}')

    if verbose >= 2:
        print()
        print(f'detected {len(uri_to_rels)} Wikidata uris according to Incident.extra_info')

    return uri_to_rels, inc_id_to_wd_uris
