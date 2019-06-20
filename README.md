# multilingual-wiki-event-pipeline

This project aims to extract information about incidents of a particular type. This information consists of structured data on the incidents from Wikidata, as well as unstructured description and supporting sources from Wikipedia. We obtain information from Wikipedia in multiple languages (currently tested with Dutch, Italian, and Japanese).


## Authors

* **Filip Ilievski** (f.ilievski@vu.nl)
* **Marten Postma** (m.c.postma@vu.nl)

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details

#### Python modules (Python 3.7 is used)
A number of external modules need to be installed, which are listed in **requirements.txt**.
Depending on how you installed Python, you can probably install the requirements using one of following commands:
```bash
pip install -r requirements.txt
```

#### Resources
A number of resources need to be downloaded. This can be done calling:
```bash
bash install.sh
```

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

The .bin files are serialized to RDF Turtle files by using the script `serialize.py`. This script reads a .bin file that contains an incident collection, and converts it to a .ttl file in the same folder. 

The settings for the experiment are stored centrally in the file `config.py`. In theory, adding a new language and/or event type requires simply a change in the config.

### Statistics

#### Stats on Dutch articles

* we get 123 incidents that fit all constraints (have a Dutch label, information on time, and location, have a description in Dutch in Wikipedia) -> step 1 & 2 & 3 & 4
* 91 out of 123 incidents have reference texts -> step 5
* The average amount of reference texts, when found, is 11.79
* Distribution of countries:

```
Countries distribution: {'Netherlands': 57, 'Belgium': 24, 'Austria': 9, 'France': 8, 'Mexico': 5, 'United States of America': 5, 'Chile': 4, 'Israel': 2, 'Croatia': 2, 'Kingdom of the Netherlands': 2, 'Romania': 1, 'Italy': 1, 'Aruba': 1, 'Peru': 1, 'Philippines': 1}
```

**Regarding the page references:** We get useful references. The number of references is approximately the same as the ones in the current wikipedia online, and the order is different.

#### Stats on Dutch and Italian reports of incidents

* In total, 261 incidents have time, location, and a label in Dutch and/or Italian, and a wikipedia description in Dutch and/or Italian -> step 1 & 2 & 3 & 4
* We obtain 267 Wikipedia pages for these 261 incidents.
* 209 of these have reference texts -> step 5
* The average amount of reference texts, when found, is 18.83
* Distribution of countries:

```
{'Italy': 110, 'Netherlands': 59, 'Belgium': 24, 'Cuba': 10, 'Austria': 9, 'France': 8, 'Mexico': 6, 'Chile': 6, 'United States of America': 5, 'Romania': 2, 'Spain': 2, 'Israel': 2, 'Croatia': 2, 'Kingdom of the Netherlands': 2, 'United Kingdom': 1, 'Russia': 1, 'Kenya': 1, 'Iran': 1, 'German Democratic Republic': 1, 'Peru': 1, 'Aruba': 1, 'Philippines': 1, 'Burkina Faso': 1, 'Venezuela': 1, 'Turkey': 1, 'Paraguay': 1, 'Costa Rica': 1, 'California': 1}
```

* Number of languages per incident (max 2 for this experiment):

```
{1: 255, 2: 6}
```

#### Stats on Dutch, Italian, and Japanese reports of incidents

* In total, 450 incidents have time, location, and a label in Dutch and/or Italian and/or Japanese, and a description in at least one of these languages -> step 1 & 2 & 3 & 4
* We get in total 469 Wikipedia pages for these 450 incidents
* 343 of these have reference texts -> step 5
* The average amount of reference texts, when found, is 17.64
* Distribution of countries:

```
{'United States of America': 149, 'Italy': 106, 'Netherlands': 55, 'Belgium': 24, 'United Kingdom': 18, 'Kingdom of Great Britain': 14, 'Cuba': 10, 'Austria': 8, 'France': 8, 'Mexico': 7, 'Spain': 7, 'Taiwan': 5, 'Chile': 5, 'Japan': 3, 'Philippines': 3, 'Romania': 2, 'Israel': 2, 'Croatia': 2, 'Venezuela': 2, 'Pakistan': 2, 'Kingdom of the Netherlands': 2, 'Canada': 1, 'Russia': 1, 'Kenya': 1, 'England': 1, 'Iran': 1, 'Czech Republic': 1, 'Iraq': 1, 'German Democratic Republic': 1, 'Burkina Faso': 1, 'Aruba': 1, 'Peru': 1, 'Bolivia': 1, 'Paraguay': 1, 'Turkey': 1, 'California': 1, 'Costa Rica': 1}
```

* Number of languages per incident (max 3 for this experiment):

```
{1: 437, 2: 7, 3: 6}
```

#### Note on the code


These statistics are produced automatically in the script `analyze.py`, by using the function `compute_stats()` of the class `IncidentCollection`:

![Alt text](img/analysis.png?raw=true "Analysis")

### Modeling

The modeling in the .ttl file is based on the SEM model. Here is an excerpt of the resulting graph:

![Alt text](img/model.png?raw=true "Model")


### Helpful links

* Wikipedia API documentation:
https://wikipedia.readthedocs.io/en/latest/code.html
