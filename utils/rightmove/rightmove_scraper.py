import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.base_scraper import BaseScraper


class RightmoveScraper(BaseScraper):
    def __init__(self, url):
        super().__init__(url)
        self.init_selenium()
        self.wait = WebDriverWait(self.driver, 10)
        self.soup = None  # Will be set after loading each page

    def scrape_property(self):
        data = {}

        # Navigate to the main property page
        self.driver.get(self.base_url)
        self.wait_for_page_load()
        # self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        self.soup = BeautifulSoup(self.driver.page_source, "lxml")
        # Extract data from the main page
        data["address"] = self.get_address()
        data["price"] = self.get_price()
        data["bedrooms"] = self.get_bedrooms()
        data["bathrooms"] = self.get_bathrooms()
        data["size"] = self.get_size()
        data["house_type"] = self.get_house_type()
        data["agent"] = self.get_agent()
        data["description"] = self.get_description()
        # data["time_on_market"] = self.get_time_on_market()
        # data["features"] = self.get_features()

        # Navigate to the images page and extract images
        data["images"] = self.get_property_images()

        # Navigate to the floorplan page and extract floorplans
        data["floorplans"] = self.get_floorplans()

        return data

    def wait_for_page_load(self):
        # Wait until the body tag is loaded
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # Optionally, wait for specific elements that you know are on the page
        time.sleep(1)  # Small delay to ensure all elements are loaded

    def get_images(self, soup):
        images = []
        image_tags = soup.find_all("img")
        for img_tag in image_tags:
            img_url = img_tag.get("src")
            if img_url and img_url not in images:
                images.append(img_url)
        return images

    def get_floorplans(self):
        floorplans = []
        # Navigate to the floorplan page
        self.driver.get(self.floor_image_url)
        self.wait_for_page_load()

        floorplan_soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Find the floorplan images
        img_tags = floorplan_soup.find_all("img", alt=re.compile("Floorplan", re.I))
        for img in img_tags:
            src = img.get("src")
            if src and "media" in src:
                floorplans.append(src)
        return floorplans

    def get_property_images(self):
        images = []
        # Navigate to the images page
        self.driver.get(self.image_url)
        self.wait_for_page_load()

        images_soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Find all image elements
        img_tags = images_soup.find_all("img")
        for img in img_tags:
            src = img.get("src")
            if src and "media" in src and "max_" not in src:
                images.append(src)
        return images

    def get_price(self):
        price_tag = self.soup.find("div", class_="_1gfnqJ3Vtd1z40MlC0MzXu")
        if price_tag:
            price_span = price_tag.find("span")
            if price_span:
                return price_span.get_text(strip=True)
        return None

    def get_bedrooms(self):
        return self.get_feature_value("BEDROOMS")

    def get_bathrooms(self):
        return self.get_feature_value("BATHROOMS")

    def get_size(self):
        return self.get_feature_value("SIZE")

    def get_house_type(self):
        return self.get_feature_value("PROPERTY TYPE")

    def get_feature_value(self, feature_name):
        dt_tags = self.soup.find_all("dt")
        for dt in dt_tags:
            span = dt.find("span")
            if span and feature_name in span.get_text():
                dd = dt.find_next_sibling("dd")
                if dd:
                    return dd.get_text(strip=True)
        return None

    def get_address(self):
        address_tag = self.soup.find("h1", itemprop="streetAddress")
        if address_tag:
            return address_tag.get_text(strip=True)
        return None

    def get_agent(self):
        agent_div = self.soup.find("div", class_="aboutAgent")
        if agent_div:
            h3_tag = agent_div.find("h3")
            if h3_tag:
                return h3_tag.get_text(strip=True)
        return None

    def get_description(self):
        h2_tag = self.soup.find("h2", text=re.compile("Description", re.I))
        if h2_tag:
            desc_div = h2_tag.find_next_sibling("div")
            if desc_div:
                return desc_div.get_text(strip=True)
        return None

    # def get_time_on_market(self, soup):
    #     # Extract the 'Added on' date
    #     div_tag = soup.find("div", text=lambda x: x and "Added on" in x)
    #     if div_tag:
    #         return div_tag.get_text(strip=True)
    #     return None

    # def get_features(self, soup):
    #     features = []
    #     features_tags = soup.find_all("li", {"class": "tick"})
    #     for feature in features_tags:
    #         features.append(feature.get_text(strip=True))
    #     return features
