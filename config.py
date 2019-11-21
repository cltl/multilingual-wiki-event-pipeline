# DEFINE INCIDENT TYPES AND LANGUAGES
#incident_types=['election']
#incident_types=['murder']
#incident_types=['conflagration', 'earthquake', 'murder']
#incident_types=['conflagration', 'earthquake', 'battle', 'murder', 'film festival', 'space flight', 'art exhibition', 'football match', 'convention', 'wrestling event', 'terrorist attack', 'tennis tournament']
incident_types=['Q132821', 'Q168983', 'Q464980', 'Q132241', 'Q4504495', 'Q3001412', 'Q220505', 'Q40244', 'Q645883', 'Q62391930']
#incident_types=['Q40231']
languages_list=['nl', 'it', 'en']

# Pilot extraction flags
must_have_all_languages=False #True
must_have_english=True #True
one_page_per_language=False # True

# Analyze pilot data only, or the full data
pilot=True #False
#pilot=False

qid2fn={'Q40231': 'change_of_leadership', 'Q132821': 'killing'} #, 'tennis tournament': 'tennis tournament'}

