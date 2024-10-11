# base_scraper.py

import os
import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


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
