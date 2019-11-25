# multilingual-wiki-event-pipeline

This project aims to extract information about incidents of a particular type. This information consists of structured data on the incidents from Wikidata, as well as unstructured description and supporting sources from Wikipedia. We obtain information from Wikipedia in multiple languages (currently tested with Dutch, Italian, English, and Japanese).


## Authors

* **Filip Ilievski** (f.ilievski@vu.nl)
* **Marten Postma** (m.c.postma@vu.nl)

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details

## Setup

### Python modules (Python 3.7 is used)
A number of external modules need to be installed, which are listed in **requirements.txt**.
Depending on how you installed Python, you can probably install the requirements using one of following commands:
```bash
pip install -r requirements.txt
```

### Resources
A number of resources need to be downloaded. This can be done calling:
```bash
bash install.sh
```

This installation takes some minutes. Grab a coffee (or two).

### Config flags

`incident_types` is a list of all event types that we want to extract information about. Example: `['conflagration', 'earthquake', 'murder']`

`languages_list` is a list of languages that we want to extract texts for. Example: `['nl', 'it', 'en']`

There are also several flags that tell the script which criteria to use for the pilot data, namely:
* `must_have_all_languages` is a Boolean variable that specifies whether the incidents must have a description in all languages from the `languages_list`.
* `must_have_english` is a Boolean variable, specifying whether English must be among the languages that describe a pilot data incident.
* `one_page_per_language` is a Boolean variable that specifies whether we only want to keep incidents with exactly one page per language from the `languages_list`.

Finally, the Boolean flag `pilot` is used to perform analysis in the script `analyze.py`, either on the full data or on the pilot data. 

## Code documentation

### Extraction steps

All extraction code can be found in the file `main.py`:

1. Get Wikidata incident IDs for an event type, like 'election' or 'murder'
2. Obtain time, location, and other predefined properties from Wikidata
3. Obtain incident name in *at least one of* a predefined set of languages
4. For each language, get Wikipedia text based on the incident name in that language, or by using the wikipedia link
5. Make a selection for a pilot data based on quality criteria
6. For each wikipedia article, get sources/reference texts from Wikipedia
7. Process each document with SpaCy
8. Enrich with entity links, based on Wikipedia hyperlinks
9. Store to NAF
10. Serialize to RDF

The final result is a processed incident collection for a set of languages and an incident type, stored in multiple ways:
* a pickle file in the `bin/` folder, containing the incident collection as a python class
* a number of NAF files in the `wiki_output` folder, containing both raw text and NLP layers
* an RDF Turtle (.ttl) representation of the extracted incidents and documents, in `bin/rdf`

The script `analyze.py` produces statistics of such incident collections.

The settings for the experiment are stored centrally in the file `config.py`. In theory, adding a new language and/or event type requires simply a change in the config.

The processing relies on the following utility files:
* `native_api_utils.py` for querying information from the Wikipedia API
* `pilot_utils.py` contains functions that select, process, enrich, and store the pilot data to NAF.
* `wikipedia_utils.py` has functions for loading of information from a preprocessed local Wikipedia dump.
* `xml_utils.py` has functions for working with XML files.

In addition, we make use of the Spacy-to-NAF functionalities.


### Paper
The file **selection_event_types.py** is used to generate a table to indicate the event type selection.


### Modeling

The modeling in the .ttl file is based on the SEM model. Here is an excerpt of the resulting graph:

![Alt text](img/model.png?raw=true "Model")


### Helpful links

* Wikipedia API documentation:
https://wikipedia.readthedocs.io/en/latest/code.html

### TODO's
* refactor classes.py to remove postprocessing
