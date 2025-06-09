import re
import time

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.base_scraper import BaseScraper
from utils.util_funcs import send_progress_update


class RightmoveScraper(BaseScraper):
    def __init__(self, url, callback_url=None, job_id=None, phone_number=None):
        super().__init__(url)
        self.init_selenium()
        self.callback_url = callback_url
        self.job_id = job_id
        self.phone_number = phone_number
        self.wait = WebDriverWait(self.driver, 10)
        self.soup = None  # Will be set after loading each page
        self.listing_type = None
        self.image_url = None
        self.floor_image_url = None

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

        # Determine the listing type based on page content
        self.listing_type = self.get_listing_type()

        # Adjust image and floorplan URLs based on listing type
        self.image_url = (
            f"{self.base_url}#/media?id=media0&ref=photoCollage&channel=RES_BUY"
        )
        self.floor_image_url = (
            f"{self.base_url}#/floorplan?activePlan=1&channel=RES_BUY"
        )

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
        data["time_on_market"] = self.get_time_on_market()
        data["features"] = self.get_features()
        data["listing_type"] = self.listing_type

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

        # Add a short delay to ensure JavaScript-rendered content is available
        time.sleep(2)

        floorplan_soup = BeautifulSoup(self.driver.page_source, "html.parser")

        # Find the floorplan images
        pattern = re.compile(r"(floorplan|floor|basement|penthouse)", re.IGNORECASE)

        # Find all image tags on the page to evaluate them
        img_tags = floorplan_soup.find_all("img")

        for img in img_tags:
            src = img.get("src", "")  # Use default "" to prevent errors
            alt = img.get("alt", "")  # Use default "" to prevent errors

            if src and ("_FLP_" in src or pattern.search(alt)):
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
        return list(set(images))

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

    def get_time_on_market(self):
        # Search for strings like "Added on" or "Reduced on" to find the date
        date_text = self.soup.find(string=re.compile("(Added on|Reduced on)", re.I))
        if date_text:
            return date_text.strip()
        else:
            return None

    def get_features(self):
        features_list = []
        h2_tag = self.soup.find("h2", text=re.compile("Key features", re.I))
        if h2_tag:
            ul_tag = h2_tag.find_next_sibling("ul")
            if ul_tag:
                li_tags = ul_tag.find_all("li")
                for li in li_tags:
                    features_list.append(li.get_text(strip=True))
        features_text = "\n".join(features_list)
        return features_text

    def get_listing_type(self):
        # Check for indicators specific to lettings
        if self.soup.find("h2", text=re.compile("Letting details", re.I)):
            return "letting"
        if self.soup.find(string=re.compile("Tenancy info", re.I)):
            return "letting"
        if self.soup.find(string=re.compile("Deposit", re.I)):
            return "letting"
        if self.soup.find("dt", text=re.compile("Let available date", re.I)):
            return "letting"

        # Check for indicators specific to sales
        if self.soup.find("dt", text=re.compile("Tenure", re.I)):
            return "sale"
        if self.soup.find(string=re.compile("Freehold|Leasehold", re.I)):
            return "sale"
        if self.soup.find(
            string=re.compile("Offers in region of|Guide Price|Offers over", re.I)
        ):
            return "sale"

        # Default to 'sale' if no specific indicators are found
        return "sale"
