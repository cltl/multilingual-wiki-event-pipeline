import pickle

import utils        
import config

if __name__ == '__main__':

    incident_types=config.incident_types
    languages_list=config.languages_list

    cartesian_product=[(x, y) for x in incident_types for y in languages_list]
    
    for incident_type, languages in cartesian_product:    
        filename=utils.make_output_filename(incident_type, 
                                                languages)

        with open(filename, 'rb') as f:
            collection=pickle.load(f)

        ttl_filename = filename.rsplit('.', 1)[0] + '.ttl'
        collection.serialize(ttl_filename)
        
        
