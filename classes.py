class Incident:

    def __init__(self, 
                incident_type,
                name,
                wdt_id,
                country_id,
                country_name,
                time,
                wiki_content='',
                language='',
                sources=''):
        self.incident_type=incident_type
        self.name=name
        self.wdt_id=wdt_id
        self.country_id=country_id
        self.country_name=country_name
        self.time=time
        self.wiki_content=wiki_content
        self.language=language
        self.sources=sources

