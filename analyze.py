import pickle

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
        num_with_sources, \
        avg_sources, \
        countries_dist, \
        numlang_dist = collection.compute_stats()

        print()
        print('*'*50)
        print('Incident type:', incident_type, '; Languages:', '-'.join(languages))
        print('*'*50)
        print('Num incidents:', num_incidents)
        print('With wiki content:', num_with_wikipedia)
        print('With sources:', num_with_sources)
        print('Avg sources:', avg_sources)
        print('Countries distribution:\n', countries_dist)
        print('Number of languages per incident:\n', numlang_dist)
        
    return
    
if __name__ == '__main__':

    incident_types=['election']
    languages_list=[['nl', 'it'],['nl']]
    #languages_list=[['nl']]


    cartesian_product=[(x, y) for x in incident_types for y in languages_list]

    compute_stats_for_all_combinations(cartesian_product)

