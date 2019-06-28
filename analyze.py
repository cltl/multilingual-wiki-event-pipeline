import pickle

import config
import utils

def compute_stats_for_all_combinations(combinations, pilot):
    """
    Compute statistics for all combinations of incident type and languages.
    """
    
    for incident_type, languages in combinations:
       
        if pilot:
            languages.append('pilot')
        filename=utils.make_output_filename(incident_type, 
                                            languages)

        with open(filename, 'rb') as f:
            collection=pickle.load(f)

        num_incidents, \
        num_with_wikipedia, \
        wiki_from_which_method, \
        num_with_sec_rt, \
        num_with_links, \
        desc_sec_rt, \
        cntr_sec_rt, \
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
        
        print('Wikipages with secondary reference texts:', num_with_sec_rt)
        print('Description of secondary reference texts:', desc_sec_rt)
        print('Distribution of secondary reference texts:', cntr_sec_rt)
        print('Wikipages with wikitext (incl. links)', num_with_links)

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
    languages_list=config.languages_list
    pilot=config.pilot

    cartesian_product=[(x, y) for x in incident_types for y in languages_list]

    compute_stats_for_all_combinations(cartesian_product, pilot)

