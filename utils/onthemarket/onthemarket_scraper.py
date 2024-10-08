import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.base_scraper import BaseScraper


class OnTheMarketScraper(BaseScraper):
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
        data["features"] = self.get_features()

        # Extract images and floorplans
        data["images"] = self.get_property_images()
        data["floorplans"] = self.get_floorplans()

        return data

    def wait_for_page_load(self):
        # Wait until the body tag is loaded
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)  # Small delay to ensure all elements are loaded

    def get_price(self):
        price_tag = self.soup.find("div", class_="otm-Price")
        if price_tag:
            price_span = price_tag.find("a", class_="price")
            if price_span:
                return price_span.get_text(strip=True)
        return None

    def get_address(self):
        address_tag = self.soup.find(
            "div", class_="text-slate h4 font-normal leading-none font-heading"
        )
        if address_tag:
            return address_tag.get_text(strip=True)
        return None

    def get_bedrooms(self):
        return self.get_feature_value("beds")

    def get_bathrooms(self):
        return self.get_feature_value("bath")

    def get_size(self):
        size_div = self.soup.find("div", string=re.compile(r"\d+\s*(sq ft|sq m)", re.I))
        if size_div:
            return size_div.get_text(strip=True)
        return None

    def get_house_type(self):
        property_type_div = self.soup.find("div", class_="otm-PropertyIcon")
        if property_type_div:
            return property_type_div.get_text(strip=True)
        return None

    def get_agent(self):
        agent_section = self.soup.find("section", class_="agent-website-button")
        if agent_section:
            agent_name = agent_section.find("a")
            if agent_name:
                return agent_name.get_text(strip=True)
        return None

    def get_description(self):
        description_section = self.soup.find("section", class_="property-description")
        if description_section:
            description_div = description_section.find(
                "div", class_="text-base text-slate"
            )
            if description_div:
                return description_div.get_text(separator="\n", strip=True)
        return None

    def get_features(self):
        features_list = []
        features_section = self.soup.find("section", class_="otm-FeaturesList")
        if features_section:
            feature_items = features_section.find_all("li")
            for item in feature_items:
                features_list.append(item.get_text(strip=True))
        return features_list

    def get_feature_value(self, feature_icon_name):
        features = self.soup.find("div", class_="otm-IconFeatures")
        if features:
            feature_items = features.find_all("div", class_="flex items-center")
            for item in feature_items:
                svg = item.find("svg", {"data-icon": feature_icon_name})
                if svg:
                    return item.get_text(strip=True)
        return None

    def get_property_images(self):
        images = []
        image_gallery = self.soup.find("div", class_="property-gallery")
        if image_gallery:
            img_tags = image_gallery.find_all("img")
            for img in img_tags:
                src = img.get("src")
                if src and src not in images:
                    images.append(src)
        return images

    def get_floorplans(self):
        floorplans = []
        floorplan_section = self.soup.find("section", class_="floorplan")
        if floorplan_section:
            img_tags = floorplan_section.find_all("img")
            for img in img_tags:
                src = img.get("src")
                if src and src not in floorplans:
                    floorplans.append(src)
        return floorplans
