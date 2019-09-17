"""
Usage:
  enrich_classes.py --bin_folder=<bin_folder> --naf_folder=<naf_folder> --verbose=<verbose> [<path_pos_mapping>]

Options:
  --bin_folder=<bin_folder> folder with bin files (instances of classes.IncidentCollection)
  --naf_folder=<naf_folder> folder where naf is stored, probably wik_output
  --verbose=<verbose>
  <path_pos_mapping> path to json file with mapping from NAF pos to preferred pos
  (only if a pos value is in the dictionary will it be used)

Example:
    python enrich_classes.py --bin_folder="bin" --naf_folder='wiki_output' --verbose=2 "config/naf_pos2fn_pos.json"
"""
import os
import json
import pickle
import utils
from docopt import docopt
from glob import glob
from xml_utils import iterable_of_lexical_items

from resources.NAF_indexer import naf_classes 

# load arguments
arguments = docopt(__doc__)
print()
print('PROVIDED ARGUMENTS')
print(arguments)
print()

verbose = int(arguments['--verbose'])
bin_folder = arguments['--bin_folder']
naf_folder = arguments['--naf_folder']

pos_mapping_path = arguments['<path_pos_mapping>']
if pos_mapping_path is not None:
    pos_mapping = json.load(open(pos_mapping_path))
else:
    pos_mapping = None 

# load subclass of ontology
utils.extract_subclass_of_ontology(wdt_sparql_url='https://query.wikidata.org/sparql',
                                   output_folder='ontology',
                                   output_basename='relations.p',
                                   verbose=verbose)
g = utils.load_ontology_as_directed_graph('ontology/relations.p',
                                          'ontology/g.p',
                                          verbose=verbose)

# add incident_collection_obj with mapping from event_type -> 'descendants' 'list_of_shortest_path' 'depth_level'
for bin_path in glob(f'{bin_folder}/*bin'):

    output_bin_path = bin_path + '.enriched'

    inc_coll_obj = pickle.load(open(bin_path, 'rb'))
    inc_coll_obj.update_incidents_with_subclass_of_info(g, top_node='wd:Q1656682', verbose=verbose)

    # index event_type -> incident_objs ids
    inc_coll_obj.event_type2wdt_ids = inc_coll_obj.get_index_event_type2wdt_ids()

    # load naf files
    naf_coll_obj = naf_classes.NAF_collection()

    for incident_obj in inc_coll_obj.incidents:
        for ref_text_obj in incident_obj.reference_texts:
            path = os.path.join(naf_folder, 
                                ref_text_obj.language, 
                                f'{ref_text_obj.name}.naf')


            if not os.path.exists(path):
                naf_obj = None
                if verbose >= 2:
                    print(f'does not exist: {path}')
            else:
                naf_obj = naf_coll_obj.add_naf_document(path, 
                                                        load_distributions=True,
                                                        pos_mapping=pos_mapping,
                                                        verbose=verbose)
                if verbose >= 3:
                    print(f'loaded {path}')
            
            ref_text_obj.naf = naf_obj
            
                    
            
    # save enriched class objects to disk
    with open(output_bin_path, 'wb') as outfile:
        pickle.dump(inc_coll_obj, outfile)


