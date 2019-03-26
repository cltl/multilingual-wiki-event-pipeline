import pickle
from collections import Counter

filename='bin/election.bin'

with open(filename, 'rb') as f:
    data=pickle.load(f)

with_sources=0
wiki_content=0
sum_sources=0
countries=[]

num_incidents=len(data)
for incident in data:
    if incident.wiki_content:
        wiki_content+=1
    if len(incident.sources):
        with_sources+=1
        sum_sources+=len(incident.sources)
    countries.append(incident.country_name)

print('Num incidents:', num_incidents)
print('With wiki content:', wiki_content)
print('With sources:', with_sources)
print('Avg sources:', sum_sources/with_sources)
print('Countries distribution:', Counter(countries))
