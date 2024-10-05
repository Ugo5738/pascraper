import os
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def get_html_content(url):
    """
    Fetch the HTML content of the page using requests.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None


def get_images_with_beautifulsoup(url):
    """
    Extract image URLs using BeautifulSoup for static HTML content.
    """
    html_content = get_html_content(url)
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "lxml")
    images = []

    # Find all image tags in the HTML
    for img_tag in soup.find_all("img"):
        img_url = img_tag.get("src")
        if img_url and "media" in img_url:  # Filter only relevant images
            images.append(img_url)

    return images


def get_images_with_selenium(url):
    """
    Extract image URLs using Selenium for dynamically loaded content.
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    driver.get(url)

    # Let the page load completely
    time.sleep(5)  # Adjust as needed to ensure full page load

    # Scroll to load more images (optional)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # Parse the page source with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, "lxml")
    driver.quit()

    images = []
    for img_tag in soup.find_all("img"):
        img_url = img_tag.get("src")
        if img_url and "media" in img_url:
            images.append(img_url)

    return images


def download_images(image_urls, save_folder="rightmove_images"):
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


def main():
    # URL of the Rightmove listing
    url = "https://www.rightmove.co.uk/properties/146759381#/media?activePlan=1&id=media4&ref=photoCollage&channel=RES_BUY"

    # Choose method based on whether content is dynamically loaded or not
    use_selenium = True  # Set to False if you know content is static

    if use_selenium:
        image_urls = get_images_with_selenium(url)
    else:
        image_urls = get_images_with_beautifulsoup(url)

    if image_urls:
        print(f"Found {len(image_urls)} images.")
        download_images(image_urls)
    else:
        print("No images found.")


if __name__ == "__main__":
    main()
