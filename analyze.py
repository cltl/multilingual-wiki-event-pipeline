import pickle

import config
import utils

def compute_stats_for_all_combinations(combinations, pilot):
    """
    Compute statistics for all combinations of incident type and languages.
    """
    bin_folder='bin'    

    for incident_type, languages in combinations:
       
        if pilot:
            filename=utils.make_output_filename(bin_folder,
                                            incident_type, 
                                            languages + ['pilot'])
        else:
            filename=utils.make_output_filename(bin_folder,
                                            incident_type,
                                            languages)

        with open(filename, 'rb') as f:
            collection=pickle.load(f)

        num_incidents, \
        num_with_wikipedia, \
        wiki_from_which_method, \
        direct_type_dist, \
        num_with_prim_rt, \
        num_with_annotations, \
        desc_prim_rt, \
        cntr_prim_rt, \
        countries_dist, \
        numwiki_dist, \
        numlang_dist, \
        extra_info_dist_agg,\
        count_occurrences,\
        count_values, \
        all_info = collection.compute_stats()

        example_incident=collection.incidents.pop()
        print(example_incident.extra_info)

        print()
        print('*'*50)
        print('Incident type:', incident_type, '; Languages:', '-'.join(languages))
        print('*'*50)
        print('Num incidents:', num_incidents)
        print('With wiki content:', num_with_wikipedia)
        print('Found by:', wiki_from_which_method)

        print('Direct type distribution', direct_type_dist)       
 
        print('Wikipages with primary reference texts:', num_with_prim_rt)
        print('Description of primary reference texts:', desc_prim_rt)
        print('Distribution of primary reference texts:', cntr_prim_rt)
        print('Wikipages with annotations', num_with_annotations)

        print('Countries distribution:\n', countries_dist)
        print('Number of Wikipages per incident:\n', numwiki_dist)
        print('Number of languages per incident:\n', numlang_dist)
        print('Distribution of properties', extra_info_dist_agg)
        print('Count of occurrences', count_occurrences)
        print('Count of values', count_values)

        print('Incidents with full info', all_info)
    return
    
if __name__ == '__main__':

    incident_types=config.incident_types
    languages_list=[config.languages_list]
    pilot=config.pilot

    cartesian_product=[(x, y) for x in incident_types for y in languages_list]

    compute_stats_for_all_combinations(cartesian_product, pilot)

