import os
import re
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BaseScraper:
    def __init__(self, url):
        self.base_url = url
        self.driver = None

    def get_html_content(self):
        """
        Fetch the HTML content of the page using requests.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching URL: {e}")
            return None

    def init_selenium(self):
        """
        Initialize Selenium WebDriver.
        """
        options = Options()
        options.add_argument("--headless")  # Run in headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-features=VizDisplayCompositor")

        # Specify the path to the Chromium executable
        options.binary_location = "/usr/bin/chromium"

        # Specify the path to the Chromium Driver
        service = Service("/usr/bin/chromedriver")

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.get(self.base_url)

        # Let the page load completely
        time.sleep(5)  # Adjust as needed to ensure full page load

        # Scroll to load more images (optional)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    def quit_selenium(self):
        """
        Quit the Selenium WebDriver.
        """
        if self.driver:
            self.driver.quit()

    def download_images(self, image_urls, save_folder="property_images"):
        """
        Download and save images to the local directory.
        """
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        for idx, img_url in enumerate(image_urls):
            try:
                img_data = requests.get(img_url).content
                img_name = os.path.join(save_folder, f"image_{idx}.jpg")
                with open(img_name, "wb") as img_file:
                    img_file.write(img_data)
                print(f"Downloaded: {img_name}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to download {img_url}: {e}")


class OnTheMarketScraper(BaseScraper):
    def __init__(self, url):
        super().__init__(url)
        self.init_selenium()
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

    def scrape_property(self):
        data = {}

        # Navigate to the main property page
        self.driver.get(self.base_url)
        self.wait_for_page_load()
        self.soup = BeautifulSoup(self.driver.page_source, "lxml")

        # Extract data from the main page
        # send_progress_update()
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
        data["floorplans"] = self.get_floorplans()
        data["images"] = self.get_property_images()

        print(data)
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
            print("Floorplan carousel not found.")

        return floorplans


def main():
    url = "https://www.onthemarket.com/details/14627179/"

    scraper = OnTheMarketScraper(url)
    scraper.scrape_property()


if __name__ == "__main__":
    main()
