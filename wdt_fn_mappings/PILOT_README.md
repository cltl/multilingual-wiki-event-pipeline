# Description pilot data project meeting Dutch FrameNet 11-7-2019

This folder contains the pilot data for the project meeting at 11-7-2019.
211 incidents are included. For each incident, we have three Wikipedia reference texts describing the incident, one in English
one in Italian, and one in Dutch.

Also, for three incidents (Q1505420, Q28036573, and Q574195), we manually added what we call **secondary reference texts**, which are texts from the *References* section of a Wikipedia article.

This folder contains two main components:
* **incidents.json**: contains both structured and unstructured data per incident
* **naf**: contains one NAF XML file per (secondary) reference text

## Incidents.json

This file contains a possible JSON representation describing each incident in the pilot data.

The WIKIDATA_EVENT_ID is the main key in the JSON file. The incident can be found online
at https://www.wikidata.org/wiki/WIKIDATA_EVENT_ID, e.g., https://www.wikidata.org/wiki/Q1065093

```json
{ WIKIDATA_EVENT_ID : {
  "event_type" : "election OR murder",
  "likely_frames": [],
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
    "title" : "title of document",
    "dct" : "document creation time (time of crawling in case of Wikipedia articles)",
    "naf_basename" : "NAF representation of file can be found in naf/BASENAME",
    "raw" : "the raw text"
  }
  }
}
```

We included two types of mapping to FrameNet, both manual.

In the first type of mapping (found in **meta_data**), we manually mapped Wikidata properties of an incident to specific frame elements. We only performed this mapping for the event type "election" and we mapped it to the Frame "Change_of_leadership":
* [succesful candidate](https://www.wikidata.org/wiki/Property:P991) is mapped to *pm:fn17-change_of_leadership@new_leader*, i.e., the frame element *new_leader* of the frame *Change_of_leadership*
* [office contested](https://www.wikidata.org/wiki/Property:P541) is mapped to *pm:fn17-change_of_leadership@role*, i.e., the frame element *role* of the frame *Change_of_leadership*
* [country](https://www.wikidata.org/wiki/Property:P17) is mapped to *pm:fn17-change_of_leadership@place*, i.e., the frame element *place* of the frame *Change_of_leadership*
* [follows](https://www.wikidata.org/wiki/Property:P155) -> [succesful candidate](https://www.wikidata.org/wiki/Property:P991) is mapped to "pm:fn17-change_of_leadership@old_leader", i.e., the frame element *old_leader* of the frame *Change_of_leadership*

In the second type of mapping (found in **likely_frames**), we find the frames that we expect to dominant this event type.


Additional explanation:
* WIKIDATA_EVENT_ID/event_type: we included two event types: elections and murders.

## [NAF](http://www.newsreader-project.eu/files/2013/01/techreport.pdf)

We used [spaCy](https://spacy.io/) to perform sentence splitting and tokenization.
After tokenization, we recreate the raw text, which ensures that we align the raw text with the tokenization. 


## Contact
* Marten Postma (m.c.postma@vu.nl)
* Filip Ilievski (f.ilievski@vu.nl)
* Piek Vossen (p.t.j.m.vossen@vu.nl)
