# Description pilot data project meeting Dutch FrameNet 11-7-2019

This folder contains the pilot data for the project meeting at 11-7-2019.
211 incidents are included. For each incidents, we have three reference texts describing the incident, one in English
one in Italian, and one in Dutch.

This folder contains two main components:
* **incidents.json**: contains both structured and unstructured data per incident
* **naf**: contains one NAF XML file per Wikipedia page

## Incidents.json

This file contains a possible JSON representation describing each incident in the pilot data.

The WIKIDATA_EVENT_ID is the main key in the JSON file. The incident can be found online
at https://www.wikidata.org/wiki/WIKIDATA_EVENT_ID, e.g., https://www.wikidata.org/wiki/Q1065093

```json
{ WIKIDATA_EVENT_ID : {
  "event_type" : "election OR murder",
  "meta_data" : {
    "pm:fn17-change_of_leadership@new_leader": [],
    "pm:fn17-change_of_leadership@old_leader": [],
    "pm:fn17-change_of_leadership@place": [],
    "pm:fn17-change_of_leadership@role": [],
    "sem:hasActor": [],
    "sem:hasPlace": [],
    "sem:hasTimeStamp": []
   
  },
  "reference_texts" : {
    "language" : "nl" | "en" : "it",
    "naf_basename" : "NAF representation of file can be found in NAF/BASENAME",
    "raw" : "the raw text"
  }
  }
}
```

Additional explanation:
* WIKIDATA_EVENT_ID/event_type: we included two event types: elections and murders.

## naf

We used [spaCy](https://spacy.io/) to perform sentence splitting and tokenization.
After tokenization, we recreate the raw text, which ensures that we align the raw text with the tokenization. 

We used the following spaCy version 2.0.0 models:
* **English**: *core_web_sm*
* **Italian**: *core_news_sm*
* **Dutch**: *core_news_sm*

## Contact
* Marten Postma (m.c.postma@vu.nl)
