class Incident:

    def __init__(self, 
                incident_type,
                wdt_id,
                country_id,
                country_name,
                time,
                reference_texts=[]):
        self.incident_type=incident_type
        self.wdt_id=wdt_id
        self.country_id=country_id
        self.country_name=country_name
        self.time=time
        self.reference_texts=reference_texts
        
class ReferenceText:
    
    def __init__(self,
                name='',
                wiki_content='',
                language='',
                sources=''):
        self.name=name
        self.wiki_content=wiki_content
        self.language=language
        self.sources=sources

