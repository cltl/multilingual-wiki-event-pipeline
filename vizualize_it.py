"""
Vizualize pilot regarding:
-structured data
-hyperlinks extracted from pilot data
-open-sesame FrameNet-based SRL system

Usage:
  vizualize_it.py --bin_folder=<bin_folder> --pilot_data=<pilot_data> --tmp_folder=<tmp_folder> --verbose=<verbose>

Options:
    --bin_folder=<bin_folder> for with .bin files (containing IncidentCollection objects from classes.py)
    --pilot_data=<pilot_data> folder containing pilot data
    --tmp_folder=<tmp_folder> folder where cached information is stored
    --verbose=<verbose> 0 nothing, 1 descriptive stats, 2 debugging information


Example:
    python vizualize_it.py --bin_folder="bin" --pilot_data="pilot_data" --tmp_folder="tmp" --verbose="2"
"""
import os
import pickle
import json
from docopt import docopt
from glob import glob

import graphviz as gv

import dbpedia_utils
import xml_utils

# load arguments
arguments = docopt(__doc__)
print()
print('PROVIDED ARGUMENTS')
print(arguments)
print()

verbose = int(arguments['--verbose'])


binfile_paths = glob(f'{arguments["--bin_folder"]}/*bin')
naf_with_entities_folder = f'{arguments["--pilot_data"]}/naf_with_entities'
naf_with_srl_folder = f'{arguments["--pilot_data"]}/naf_with_srl/NAF'
path_interlanguage_links = f'{arguments["--tmp_folder"]}/interlanglinks.json'

if verbose >= 2:
    print(f'bin files', binfile_paths)
    print(f'path interlanguage links: {path_interlanguage_links}')

# load xml
lang2xml_paths = xml_utils.load_lang2paths(binfile_paths, naf_with_entities_folder, verbose=verbose)
en_entity2occurrences = xml_utils.get_entity2occurrences(paths=lang2xml_paths['en'], verbose=verbose)
nl_entity2occurrences = xml_utils.get_entity2occurrences(paths=lang2xml_paths['nl'], verbose=verbose)
it_entity2occurrences = xml_utils.get_entity2occurrences(paths=lang2xml_paths['it'], verbose=verbose)

# load interlanguage links
page_names = list(en_entity2occurrences.keys())
if not os.path.exists(path_interlanguage_links):
    result = dbpedia_utils.get_interlanguage_links(page_names, verbose=verbose)
    with open(path_interlanguage_links, 'w') as outfile:
        json.dump(result, outfile)
else:
    result = json.load(open(path_interlanguage_links))

mapping = {
    'pm:fn17-change_of_leadership@new_leader' : 'succesful candidate',
    'pm:fn17-change_of_leadership@old_leader' : 'succesful candidate of previous election',
    'pm:fn17-change_of_leadership@role' : 'office contested',
    'pm:fn17-change_of_leadership@place' : 'country'
}


# vizualize it
interesting = set()

for binfile_path in binfile_paths:
    with open(binfile_path, 'rb') as infile:
        collection = pickle.load(infile)
        for incident in collection.incidents:
            g_style = ['compound=true;']
            g = gv.Digraph(format='svg', name='G', body=g_style)

            nodes_to_add = set()
            edges_to_add = set()

            relevant_documents = {ref_text_obj.name for ref_text_obj in incident.reference_texts}

            english_docs = [ref_text_obj.name
                            for ref_text_obj in incident.reference_texts
                            if ref_text_obj.language == 'en']
            english_doc = english_docs[0]

            entity2frames_and_roles = xml_utils.get_entity2frames_and_roles(naf_with_entities_folder,
                                                                            naf_with_srl_folder,
                                                                            english_doc)

            g.node(incident.wdt_id)

            for key, set_value in incident.extra_info.items():

                value = next(iter(set_value))
                link, label = value.split(' | ')
                if key == 'sem:hasTimeStamp':
                    label = link.split('T')[0]
                    link = label


                if link.startswith('http:'):
                    link = link.split('www.')[1]

                g.node(link,
                       label=label,
                       tooltip=link)

                if key in mapping:
                    edge_label = mapping[key]
                else:
                    edge_label = key

                g.edge(incident.wdt_id, link, edgetooltip=edge_label)

                if label in entity2frames_and_roles:
                    interesting.add(incident.wdt_id)
                    for frame, role in entity2frames_and_roles[label]:

                        if role == 'predicate':
                            print(incident.wdt_id, frame, role, label)
                        node_label = f'FRAME-{frame}-ROLE-{role}'
                        g.edge(link, node_label, edgetooltip=english_doc)

                if label in en_entity2occurrences:

                    # check mapping
                    if label in result:
                        langlinks = result[label]
                        langlinks['en'] = label

                        for lang, occurrences in [('nl', nl_entity2occurrences),
                                                  ('it', it_entity2occurrences),
                                                  ('en', en_entity2occurrences)]:
                            if lang in langlinks:
                                occurrences = occurrences[langlinks[lang]]
                                if occurrences:
                                    for basename, identifier, mention in occurrences:
                                        if basename in relevant_documents:

                                            nodes_to_add.add((identifier, mention, identifier))
                                            edges_to_add.add(((identifier, mention, identifier),
                                                              link)
                                                             )

            for identifier, mention, identifier in nodes_to_add:
                g.node(identifier,
                       label=mention,
                       tooltip=identifier)

            for (identifier, mention, identifier), link in edges_to_add:
                g.edge(identifier, link)

            #print(edges_to_add)
            s = gv.Source(g.source, format='svg')
            s.render(f'dot/{incident.wdt_id}')


print(interesting)