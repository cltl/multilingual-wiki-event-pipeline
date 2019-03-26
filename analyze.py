import pickle
from collections import Counter

import utils

incident_type='election'
#languages=['nl', 'it']
languages=['nl']

filename=utils.make_output_filename(incident_type, languages)

with open(filename, 'rb') as f:
    data=pickle.load(f)

with_sources=0
wiki_content=0
sum_sources=0
countries=[]

num_languages=[]

num_incidents=len(data)
for incident in data:
    print(incident.wdt_id, incident.country_name)
    for ref_text in incident.reference_texts:
        print(ref_text.name, ref_text.language)
        if ref_text.wiki_content:
            wiki_content+=1
        if len(ref_text.sources):
            with_sources+=1
            sum_sources+=len(ref_text.sources)
    num_languages.append(len(incident.reference_texts))
    countries.append(incident.country_name)

print('Num incidents:', num_incidents)
print('With wiki content:', wiki_content)
print('With sources:', with_sources)
print('Avg sources:', sum_sources/with_sources)
print('Countries distribution:', Counter(countries))
print('Number of languages per incident:', Counter(num_languages))
