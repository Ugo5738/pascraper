from bs4 import BeautifulSoup
from utils.base_scraper import BaseScraper


class ZooplaScraper(BaseScraper):
    def __init__(self, url):
        super().__init__(url)
        self.property_details = {}

    def scrape(self):
        self.init_selenium()
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        self.extract_details(soup)
        self.quit_selenium()
        return self.property_details

    def extract_details(self, soup):
        # Implement similar methods as in RightmoveScraper
        pass


# Similar implementation for OnTheMarketScraper
