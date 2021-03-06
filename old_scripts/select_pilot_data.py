import time
import pickle
import json
import re

import classes
import config
import utils
import native_api_utils as api

eventtype2json={'election': 'change_of_leadership', 'murder': 'killing'}

def remove_incidents_with_missing_FEs(incidents, event_type):
    new_incidents=[]

    jsonfilename='wdt_fn_mappings/%s.json' % eventtype2json[event_type]

    with open(jsonfilename, 'rb') as f:
        wdt_fn_mappings_COL=json.load(f)

    all_frame_elements=set(wdt_fn_mappings_COL.keys())

    for incident in incidents:
        extra_info_keys=set(incident.extra_info.keys())
        if extra_info_keys==all_frame_elements:
            new_incidents.append(incident)
    return new_incidents


def check_ref_text(rt, min_chars=100, max_chars=10000):
    num_chars=len(rt.content)
    if num_chars<min_chars or num_chars>max_chars:
        return False
    if re.match(r'.*[1-2]([0-9]){3}-[1-2]([0-9]){3}.*$', rt.name):
        print(rt.name)
        return False
    return True

def create_pilot_data(data):
    pilot_incidents=set()

    cached={}

    data.incidents=remove_incidents_with_missing_FEs(data.incidents, data.incident_type)
    for incident in data.incidents:
        langs=set()
        incident.reference_texts=utils.deduplicate_ref_texts(incident.reference_texts)
        new_ref_texts=[]
        for ref_text in incident.reference_texts:
            ref_text.content=ref_text.content.split('==')[0].strip() # first section
            if check_ref_text(ref_text):
                langs.add(ref_text.language)
                new_ref_texts.append(ref_text)
        incident.reference_texts=new_ref_texts
        if 'en' in langs and 'it' in langs and 'nl' in langs and len(new_ref_texts)==3:
            for ref_text in incident.reference_texts:
                if not ref_text.uri:
                    ref_text.uri=api.get_uri_from_title(ref_text.name, ref_text.language)
                    print(ref_text.name, ref_text.language, 'URI', ref_text.uri)
            pilot_incidents.add(incident)
            for p, v_set in incident.extra_info.items():
                new_v_set=set()
                for v in v_set:
                    if '|' not in v:
                        label=''
                        q_id=v.split('/')[-1]
                        if q_id in cached.keys():
                            label=cached[q_id]
                            print('cached', q_id)
                        elif v.startswith('http'):
                            print('no label for', v)
                            label=utils.obtain_label(q_id)
                            time.sleep(1)
                            cached[q_id]=label
                        v+=' | ' + label
                        new_v_set.add(v)
                    else:
                        new_v_set.add(v)
                incident.extra_info[p]=new_v_set
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
