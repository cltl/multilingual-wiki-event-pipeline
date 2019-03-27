# multilingual-wiki-event-pipeline

This project aims to extract information about incidents of a particular type. This information consists of structured data on the incidents from Wikidata, as well as unstructured description and supporting sources from Wikipedia. We obtain information from Wikipedia in multiple languages (currently tested with Dutch and Italian).

### Steps

1. Get Wikidata incident IDs for an event type, like 'election'
2. Obtain time, location from Wikidata
3. Obtain incident name in *at least one of* a predefined set of languages
4. For each language, get Wikipedia text based on the incident name in that language
5. For each language, get sources/reference texts from Wikipedia

### Code

All extraction code can be found in the file `extract.py`. Steps 1, 2, and 3 are covered by the function `retrieve_incidents_per_type` which queries Wikidata, whereas the steps 4 and 5 are covered by the function `obtain_wiki_text_and_references` which queries Wikipedia.

The final result is an incident collection for a set of languages and an incident type. This collection is stored in a pickle file in the `bin/` folder. 

The script `analyze.py` produces statistics of such incident collections.

### Helpful links

* Wikipedia API documentation:
https://wikipedia.readthedocs.io/en/latest/code.html

### Statistics

#### Stats on Dutch articles

* we get 147 incidents that fit all constraints (have a Dutch label, information on time, and location) -> step 1 & 2 & 3
* 133 out of 147 incidents have a description in Dutch in Wikipedia (that we can obtain automatically) -> step 4
* 101 out of 147 incidents have reference texts -> step 5
* The average amount of reference texts, when found, is 13.11
* Distribution of countries:

```
Countries distribution: Counter({'Netherlands': 64, 'Belgium': 26, 'Austria': 9, 'France': 8, 'Italy': 8, 'Mexico': 6, 'Chile': 6, 'United States of America': 5, 'Romania': 2, 'Israel': 2, 'Croatia': 2, 'Sweden': 2, 'Kingdom of the Netherlands': 2, 'Spain': 1, 'Peru': 1, 'Aruba': 1, 'Venezuela': 1, 'Philippines': 1})
```

**Regarding the page references:** We get useful references. The number of references is approximately the same as the ones in the current wikipedia online, and the order is different.

#### Stats on Dutch and Italian reports of incidents

* In total, 286 incidents have time, location, and a label in Dutch and/or Italian -> step 1 & 2
* For these incidents, we have 298 labels in total for Dutch and Italian from Wikidata -> step 3
* For 268 out of 298 labels we can obtain the Wikipedia page -> step 4
* 212 of these have reference texts -> step 5
* The average amount of reference texts, when found, is 17.83
* Distribution of countries:

```
{'Italy': 121, 'Netherlands': 64, 'Belgium': 26, 'Cuba': 10, 'Austria': 9, 'France': 9, 'Mexico': 7, 'United States of America': 7, 'Chile': 6, 'Spain': 2, 'Croatia': 2, 'Romania': 2, 'Israel': 2, 'Kingdom of the Netherlands': 2, 'Sweden': 2, 'United Kingdom': 1, 'Russia': 1, 'Kenya': 1, 'Peru': 1, 'Iran': 1, 'German Democratic Republic': 1, 'Aruba': 1, 'Burkina Faso': 1, 'Argentina': 1, 'Turkey': 1, 'Venezuela': 1, 'Paraguay': 1, 'California': 1, 'Costa Rica': 1, 'Philippines': 1}
```

* Number of languages per incident (max 2 for this experiment):

```
{1: 274, 2: 12}
```

#### Note on the code


These statistics are produced automatically in the script `analyze.py`, by using the function `compute_stats()` of the class `IncidentCollection`:

![Alt text](img/analysis.png?raw=true "Analysis")
