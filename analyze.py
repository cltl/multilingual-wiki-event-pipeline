import pickle

import config
import utils

def compute_stats_for_all_combinations(combinations):
    """
    Compute statistics for all combinations of incident type and languages.
    """
    
    for incident_type, languages in combinations:

        filename=utils.make_output_filename(incident_type, 
                                            languages)

        with open(filename, 'rb') as f:
            collection=pickle.load(f)

        num_incidents, \
        num_with_wikipedia, \
        wiki_from_which_method, \
        num_with_sources, \
        avg_sources, \
        countries_dist, \
        numwiki_dist, \
        numlang_dist, \
        extra_info_dist_agg,\
        count_occurrences = collection.compute_stats()

        

        print()
        print('*'*50)
        print('Incident type:', incident_type, '; Languages:', '-'.join(languages))
        print('*'*50)
        print('Num incidents:', num_incidents)
        print('With wiki content:', num_with_wikipedia)
        print('Found by:', wiki_from_which_method)
        
        print('With sources:', num_with_sources)
        print('Avg sources:', avg_sources)
        print('Countries distribution:\n', countries_dist)
        print('Number of Wikipages per incident:\n', numwiki_dist)
        print('Number of languages per incident:\n', numlang_dist)
        print('Distribution of properties', extra_info_dist_agg)
        print('Count of occurrences', count_occurrences)
    return
    
if __name__ == '__main__':

    incident_types=config.incident_types
    languages_list=config.languages_list

    cartesian_product=[(x, y) for x in incident_types for y in languages_list]

    compute_stats_for_all_combinations(cartesian_product)

