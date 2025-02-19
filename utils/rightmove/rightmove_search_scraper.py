import urllib.parse

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.base_scraper import BaseScraper


class RightmoveSearchScraper(BaseScraper):
    def __init__(self, search_params):
        self.search_params = search_params
        self.base_search_url = (
            "https://www.rightmove.co.uk/property-for-sale/find.html?"
        )
        super().__init__(self.construct_search_url())
        self.driver = None

    def construct_search_url(self, index=0):
        params = {
            "locationIdentifier": self.search_params.get("location", ""),
            "minPrice": self.search_params.get("min_price", ""),
            "maxPrice": self.search_params.get("max_price", ""),
            "minBedrooms": self.search_params.get("min_bedrooms", ""),
            "index": index,
        }
        return self.base_search_url + urllib.parse.urlencode(params)

    def scrape_search_results(self):
        self.init_selenium()
        property_urls = []
        try:
            index = 0
            while True:
                url = self.construct_search_url(index)
                self.driver.get(url)
                self.wait_for_page_load()
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                urls = self.extract_property_urls(soup)
                if not urls:
                    break
                property_urls.extend(urls)
                if not self.has_next_page(soup):
                    break
                index += 24
        finally:
            self.quit_selenium()
        return property_urls

    def extract_property_urls(self, soup):
        urls = []
        for link in soup.select('a.propertyCard-link[href^="/properties/"]'):
            href = link.get("href")
            urls.append(f"https://www.rightmove.co.uk{href}")
        return urls

    def has_next_page(self, soup):
        next_button = soup.find("button", {"class": "pagination-direction--next"})
        return next_button and "disabled" not in next_button.get("class", [])

    def wait_for_page_load(self):
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".propertyCard"))
        )
