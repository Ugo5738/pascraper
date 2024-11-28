import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from pascraper.config.logging_config import configure_logger
from utils.base_scraper import BaseScraper
from utils.util_funcs import send_progress_update

logger = configure_logger(__name__)


class OnTheMarketScraper(BaseScraper):
    def __init__(self, url, callback_url=None, job_id=None, phone_number=None):
        super().__init__(url)
        self.init_selenium()
        self.callback_url = callback_url
        self.job_id = job_id
        self.phone_number = phone_number
        match = re.search(r"/details/(\d+)", url)
        if match:
            self.property_id = match.group(1)
            self.image_url = (
                f"https://www.onthemarket.com/details/{self.property_id}/#/photos/1"
            )
            self.floorplan_url = (
                f"https://www.onthemarket.com/details/{self.property_id}/#/floorplans/1"
            )
        else:
            raise ValueError("Invalid OnTheMarket URL format: Property ID not found.")

        self.wait = WebDriverWait(self.driver, 10)
        self.soup = None  # Will be set after loading each page

    def send_progress(self, message, current_step, total_steps, stage="First Step"):
        if self.callback_url and self.job_id:
            progress = (current_step / total_steps) * 100
            send_progress_update(
                self.callback_url,
                self.job_id,
                {
                    "stage": stage,
                    "message": message,
                    "progress": progress,
                },
                self.phone_number,
            )

    def scrape_property(self):
        data = {}
        total_steps = 4  # Adjust based on the number of steps in the process
        current_step = 0

        # Step 1: Navigate to the main property page
        current_step += 1
        self.send_progress(
            "Navigating to main property page", current_step, total_steps
        )
        self.driver.get(self.base_url)
        self.wait_for_page_load()
        self.soup = BeautifulSoup(self.driver.page_source, "lxml")

        # Step 2: Extract data from the main page
        current_step += 1
        self.send_progress(
            "Taking a look at the main page data", current_step, total_steps
        )
        data["address"] = self.get_address()
        data["price"] = self.get_price()
        data["bedrooms"] = self.get_bedrooms()
        data["bathrooms"] = self.get_bathrooms()
        data["size"] = self.get_size()
        data["house_type"] = self.get_house_type()
        data["agent"] = self.get_agent()
        data["description"] = self.get_description()
        data["features"] = self.get_features()

        # Step 3: Navigate to the images page and extract images
        current_step += 1
        self.send_progress(
            "Taking a look at the property images", current_step, total_steps
        )
        data["images"] = self.get_property_images()

        # Step 4: Navigate to the floorplan page and extract floorplans
        current_step += 1
        self.send_progress("Taking a look at the floorplans", current_step, total_steps)
        data["floorplans"] = self.get_floorplans()

        return data

    def wait_for_page_load(self):
        # Wait until the body tag is loaded
        self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Small delay to ensure all elements are loaded

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
        unique_images = set()

        # Navigate to the image gallery page
        self.driver.get(self.image_url)
        self.wait_for_page_load()

        # Wait for the page to fully load
        time.sleep(2)  # Adjust as necessary

        # Parse the page source
        self.soup = BeautifulSoup(self.driver.page_source, "lxml")

        # Find all 'li' elements with class 'slide'
        image_elements = self.soup.find_all("li", class_="slide")
        for li in image_elements:
            picture_tag = li.find("picture")
            if picture_tag:
                img_tag = picture_tag.find("img")
                if img_tag:
                    src_img = img_tag.get("src")
                    if src_img and "logo" not in src_img:
                        # Normalize the URL by removing the extension
                        base_url = src_img.rsplit(".", 1)[0]
                        if base_url not in unique_images:
                            unique_images.add(base_url)
                            images.append(src_img)

        return images

    def get_floorplans(self):
        floorplans = []

        self.driver.get(self.floorplan_url)
        self.wait_for_page_load()

        # Give time for the page to fully load
        time.sleep(2)  # Adjust as necessary

        # Parse the page source
        soup = BeautifulSoup(self.driver.page_source, "lxml")

        # Find the carousel root for floorplans
        carousel_root = soup.find("div", class_="carousel-root floorplans")
        if carousel_root:
            # Find all 'img' tags within the carousel with alt="Floorplan"
            img_tags = carousel_root.find_all("img", alt="Floorplan")
            for img in img_tags:
                src = img.get("src")
                if src and src not in floorplans:
                    floorplans.append(src)
        else:
            logger.info("Floorplan carousel not found.")

        return floorplans
