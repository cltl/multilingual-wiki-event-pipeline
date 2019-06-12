import pickle
import json
import re

import classes
import config
import utils


def deduplicate_ref_texts(ref_texts):
    new_ref_texts=[]
    for rt in ref_texts:
        to_keep=True
        for other_rt in ref_texts:
            if rt.language==other_rt.language and rt.name<other_rt.name:
                if rt.wiki_content==other_rt.wiki_content:
                    to_keep=False
                    break
        if to_keep:
            new_ref_texts.append(rt)
    return new_ref_texts
     
def remove_incidents_with_missing_FEs(incidents):
    new_incidents=[]
    with open('wdt_fn_mappings/change_of_leadership.json', 'rb') as r:
        wdt_fn_mappings_COL=json.load(r)
    all_frame_elements=set(wdt_fn_mappings_COL.keys())

    for incident in incidents:
        extra_info_keys=set(incident.extra_info.keys())
        if extra_info_keys==all_frame_elements:
            new_incidents.append(incident)
    return new_incidents


def check_ref_text(rt, min_chars=100, max_chars=10000):
    num_chars=len(rt.wiki_content)
    if num_chars<min_chars or num_chars>max_chars:
        return False
        #print(rt.wiki_content)
    #regex='.*[1-2]([0-9]){3}-[1-2]([0-9]){3}.*$'
    if re.match(r'.*[1-2]([0-9]){3}-[1-2]([0-9]){3}.*$', rt.name):
        print(rt.name)
        return False
    return True

def create_pilot_data(data):
    pilot_incidents=set()

    data.incidents=remove_incidents_with_missing_FEs(data.incidents)
    for incident in data.incidents:
        langs=set()
        incident.reference_texts=deduplicate_ref_texts(incident.reference_texts)
        new_ref_texts=[]
        for ref_text in incident.reference_texts:
            ref_text.wiki_content=ref_text.wiki_content.split('==')[0].strip() # first section
            if check_ref_text(ref_text):
                langs.add(ref_text.language)
                new_ref_texts.append(ref_text)
        incident.reference_texts=new_ref_texts
        if 'en' in langs and 'it' in langs and 'nl' in langs and len(new_ref_texts)==3:
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
