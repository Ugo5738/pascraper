import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.base_scraper import BaseScraper


class ZooplaScraper(BaseScraper):
    def __init__(self, url):
        super().__init__(url)
        self.init_selenium()
        self.wait = WebDriverWait(self.driver, 20)  # Increased wait time
        self.soup = None  # Will be set after loading each page

    def scrape_property(self):
        data = {}

        # Navigate to the main property page
        self.driver.get(self.base_url)
        self.wait_for_page_load()
        self.handle_cookies_popup()
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
        data["images"] = self.get_property_images()
        data["floorplans"] = self.get_floorplans()

        self.quit_selenium()
        return data

    def wait_for_page_load(self):
        # Wait until the main content is loaded
        self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-testid='listing-details-page']")
            )
        )
        time.sleep(1)  # Small delay to ensure all elements are loaded

    def handle_cookies_popup(self):
        # Handle the cookies acceptance popup if it appears
        try:
            accept_button = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Accept all cookies')]")
                )
            )
            accept_button.click()
        except Exception:
            pass  # If the popup doesn't appear, proceed

    def get_price(self):
        price_tag = self.soup.find("p", attrs={"data-testid": "price"})
        if price_tag:
            return price_tag.get_text(strip=True)
        return None

    def get_address(self):
        address_tag = self.soup.find("address", attrs={"data-testid": "address-label"})
        if address_tag:
            return address_tag.get_text(strip=True)
        return None

    def get_bedrooms(self):
        return self.get_feature_value("Bedrooms")

    def get_bathrooms(self):
        return self.get_feature_value("Bathrooms")

    def get_size(self):
        # Size may not always be present
        size_value = self.get_feature_value("sq. ft")
        if size_value:
            return size_value
        return None

    def get_feature_value(self, feature_name):
        # Find all property features
        features_section = self.soup.find(
            "div", attrs={"data-testid": "listing-summary-details-heading"}
        )
        if features_section:
            feature_items = features_section.find_next("div").find_all(
                "div", recursive=False
            )
            for item in feature_items:
                text = item.get_text(separator=" ", strip=True)
                if feature_name in text:
                    # Extract the number preceding the feature name
                    match = re.search(r"(\d+)\s*" + re.escape(feature_name), text, re.I)
                    if match:
                        return match.group(1)
        return None

    def get_house_type(self):
        # Extract house type from the title
        title_tag = self.soup.find("p", {"data-testid": "title-label"})
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # Format is usually '1 bed flat to rent'
            match = re.search(r"\d+\s+bed\s+(.+?)\s+to\s+rent", title_text, re.I)
            if match:
                return match.group(1).strip()
        return None

    def get_agent(self):
        agent_tag = self.soup.find("p", class_=re.compile(r"^_1fnpa5a3"))
        if agent_tag:
            return agent_tag.get_text(strip=True)
        return None

    def get_description(self):
        desc_div = self.soup.find("div", {"data-testid": "listing_description"})
        if desc_div:
            paragraphs = desc_div.find_all("p")
            description_text = "\n".join([p.get_text(strip=True) for p in paragraphs])
            if description_text:
                return description_text
            # Fallback to any text within the div
            return desc_div.get_text(separator="\n", strip=True)
        return None

    def get_property_images(self):
        images = []
        # Find the gallery section
        gallery_section = self.soup.find(
            "section", {"aria-labelledby": "listing-gallery-heading"}
        )
        if gallery_section:
            # Find all images within the gallery
            img_tags = gallery_section.find_all(
                "img", {"class": re.compile(r"^_1rk40755")}
            )
            for img_tag in img_tags:
                img_src = img_tag.get("src")
                if img_src and img_src not in images:
                    images.append(img_src)
        return images

    def get_floorplans(self):
        floorplans = []
        # Find the section with floor plans
        floorplan_heading = self.soup.find("h3", string=re.compile("Floor plans", re.I))
        if floorplan_heading:
            floorplan_div = floorplan_heading.find_next("div")
            if floorplan_div:
                img_tags = floorplan_div.find_all("img")
                for img_tag in img_tags:
                    img_src = img_tag.get("src")
                    if img_src and img_src not in floorplans:
                        floorplans.append(img_src)
        return floorplans
