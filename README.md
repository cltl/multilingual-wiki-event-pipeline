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

### Extraction Steps

All extraction code can be found in the file `extract.py`:

1. Get Wikidata incident IDs for an event type, like 'election' or 'murder'
2. Obtain time, location, and other predefined properties from Wikidata
3. Obtain incident name in *at least one of* a predefined set of languages
4. For each language, get Wikipedia text based on the incident name in that language, or by using the wikipedia link
5. For each wikipedia article, get sources/reference texts from Wikipedia

The final result is an incident collection for a set of languages and an incident type. This collection is stored in a pickle file in the `bin/` folder. 

The script `analyze.py` produces statistics of such incident collections.

The .bin files are serialized to RDF Turtle files by using the script `serialize.py`. This script reads a .bin file that contains an incident collection, and converts it to a .ttl file in the same folder. 

The settings for the experiment are stored centrally in the file `config.py`. In theory, adding a new language and/or event type requires simply a change in the config.

The pilot data is selected in the following way:
1. the script `select_pilot_data.py` selects a subset of the incidents and reference texts that have the most complete information.
2. the script `create_pilot_data.py` creates a NAF representation of the pilot reference texts. During this step, the text is processed by spacy to extract token information.
3. the script `enrich_pilot_data.py` adds entity information to the NAFs. Namely, the hyperlinks extracted during the crawling process are now merged within the NAF files and stored in the entity layer.

### Statistics

#### Elections

...

#### Murders

...

### Modeling

The modeling in the .ttl file is based on the SEM model. Here is an excerpt of the resulting graph:

![Alt text](img/model.png?raw=true "Model")


### Helpful links

* Wikipedia API documentation:
https://wikipedia.readthedocs.io/en/latest/code.html
