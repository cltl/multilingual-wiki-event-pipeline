import pickle

import classes
import config
import utils


def create_pilot_data(data):
    pilot_incidents=set()

    for incident in data.incidents:
        langs=set()
        for ref_text in incident.reference_texts:
            langs.add(ref_text.language)
        if 'en' in langs and 'it' in langs and 'nl' in langs:
            pilot_incidents.add(incident)

    print(len(pilot_incidents))
    return pilot_incidents

incident_types=config.incident_types
languages_list=config.languages_list

incident_type=incident_types[0]
languages=languages_list[0]

filename=utils.make_output_filename(incident_type, languages)

with open(filename, 'rb') as f:
    collection=pickle.load(f)

pilots=create_pilot_data(collection)

pilot_collection=classes.IncidentCollection(incidents=pilots,
		     incident_type=incident_type,
		     languages=languages)

languages.append('pilot')
out_file=utils.make_output_filename(incident_type, languages)

with open(out_file, 'wb') as of:
    pickle.dump(pilot_collection, of)
