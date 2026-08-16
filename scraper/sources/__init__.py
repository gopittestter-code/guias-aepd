from .aepd import AEPDScraper
from .aepd_guides import AEPDGuidesScraper
from .ccn_cert import CCNCertScraper
from .ccn_cert_guides import CCNCertGuidesScraper
from .incibe import IncibeScraper
from .edps import EDPSscraper

ALL_SCRAPERS = [
    AEPDScraper,
    AEPDGuidesScraper,
    CCNCertScraper,
    CCNCertGuidesScraper,
    IncibeScraper,
    EDPSscraper,
]
