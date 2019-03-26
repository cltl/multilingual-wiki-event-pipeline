# wiki-event-pipeline

This project aims to extract information about incidents of a particular type. This information consists of structured data on the incidents from Wikidata, as well as unstructured description and supporting sources from Wikipedia.

### Steps

1. Get Wikidata incident IDs for an event type, like 'election'
2. Obtain time, location from Wikidata
3. Obtain incident name in *at least one of* a predefined set of languages
4. For each language, get Wikipedia text based on the incident name in that language
5. For each language, get sources/reference texts from Wikipedia

### Code

All extraction code can be found in the file `extract.py`. Steps 1, 2, and 3 are covered by the function `retrieve_incidents_per_type` which queries Wikidata, whereas the steps 4 and 5 are covered by the function `obtain_wiki_text_and_references` which queries Wikipedia.

The final result is stored in a pickle file in the `bin/` folder. 

### Helpful links

* Wikipedia API documentation:
https://wikipedia.readthedocs.io/en/latest/code.html

### Findings/notes

**Stats on Dutch articles:**

* we get 171 incidents that fit all constraints (have a Dutch label, information on time, and location) -> step 1 & 2
* 149 out of 171 incidents have a description in Dutch in Wikipedia (that we can obtain automatically) -> step 3
* 115 out of 171 incidents have reference texts -> step 4
* The average amount of reference texts, when found, is 10.52
* Distribution of countries:

```
Countries distribution: Counter({'Netherlands': 71, 'Belgium': 22, 'Austria': 10, 'Italy': 9, 'France': 8, 'Mexico': 6, 'Chile': 6, 'United States of America': 5, 'Latvia': 3, 'Spain': 3, 'Croatia': 3, 'Sweden': 3, 'Greece': 2, 'Romania': 2, 'Israel': 2, 'Bulgaria': 2, 'Slovenia': 1, 'Ireland': 1, 'Czech Republic': 1, 'Malta': 1, 'Slovakia': 1, 'Cyprus': 1, 'Portugal': 1, 'Lithuania': 1, 'Hungary': 1, 'Estonia': 1, 'Peru': 1, 'Kingdom of the Netherlands': 1, 'Aruba': 1, 'Venezuela': 1})
```

**Regarding the page references:** We get useful references. The number of references is approximately the same as the ones in the current wikipedia online, and the order is different.
