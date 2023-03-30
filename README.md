# multilingual-wiki-event-pipeline

This project aims to extract information about incidents of a particular event type.
This information consists of structured data on the incidents from Wikidata, as well as unstructured description and supporting sources from Wikipedia.
We obtain information from Wikipedia in multiple languages (currently tested with Dutch, Italian, English, and Japanese).


## License
This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details

## Setup

### Python modules (Python 3.6 is used)

Update: The current version has been updated to run with python 3.10, the new spacy_to_naf module and the current version of newsplease (1.5.22).

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

### Configuration

Please run
```python
python main.py -h
```
To get information about how to use MWEP.

We make use of docopt to provide arguments to the Python module **main.py**.
The first argument is **--config_path**, for which a path to a JSON file should be provided (see config/mwep_settings.json for an example).
* **processing**:
    * **must_have_all_languages**: if set to True, an Incident is only included if a Wikipedia text is found for all specified languages.
    * **must_have_english**: if set to True, an Incident is only added if the text of the English Wikipedia page was available.
    * **one_page_per_language**: if set to True, we only include Incidents for which we have available one page per language (due to the API calling, it can occur than we find two Wikipedia pages for the same language)
* **newsplease**: this is the library we use to crawl Wikipedia sources (is very slow, will only work with a small number of Incidents)
    * **excluded_domains**: exclude Wikipedia sources from these domains
    * **title_required**: if set to True, newsplease needs to detect a title for the Wikipedia source
    * **num_chars_range**: sets the range of characters allowed, i.e., how many characters is the Wikipedia source text to have?
    * **startswith**: the Wikipedia source url has to start with this prefix
    * **timeout**: timeout after this number of seconds for a query to find the Waybach Machine URI
* **event_type_matching**: direct_match | subsumed_by. In the case of direct_match, only event types that have this event type directly are retrieved. If subsumed_by is chosen, all descendant event type according to the Wikidata ontology are also retrieved.
* **wiki_langlinks_paths**: please set this to "resources/merged_indices.p" (is downloaded when calling install.sh)
* **wiki_folder**: "resources/Wikipedia_Reader/wiki" (is downloaded when calling install.sh)
* **naf_output_folder**: folder where NAF files will be stored
* **rdf_folder**: folder where SEM RDF will be stored
* **bin_folder**: this will contain the pickled IncidentCollection objects (see classes.py)
* **json_folder**: this will contain the mappings between structured and unstructured data
* **spacy_models**: the names of the spaCy models used per language.

### Extraction steps

All extraction code can be found in the file `main.py`:

1. Get Wikidata incident IDs for an event type, like Q40231 (election)
2. Obtain time, location, and other predefined properties from Wikidata
3. Obtain incident name in *at least one of* a predefined set of languages
4. For each language, get Wikipedia text based on the incident name in that language, or by using the wikipedia link
5. For each wikipedia article, get sources/reference texts from Wikipedia
6. Process each document with SpaCy
7. Enrich with entity links, based on Wikipedia hyperlinks
8. Store to NAF

The final result is a processed incident collection for a set of languages and an incident type, stored in multiple ways:
* a pickle file in the `bin/` folder, containing the incident collection as a python class
* a number of NAF files in the `wiki_output` folder, containing both raw text and NLP layers


### Helpful links

* Wikipedia API documentation:
https://wikipedia.readthedocs.io/en/latest/code.html
