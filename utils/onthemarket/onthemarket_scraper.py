from bs4 import BeautifulSoup
from utils.base_scraper import BaseScraper


class OnTheMarketScraper(BaseScraper):
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
        self.property_details["images"] = self.get_images(soup)
        self.property_details["floorplans"] = self.get_floorplans(soup)
        self.property_details["price"] = self.get_price(soup)
        self.property_details["bedrooms"] = self.get_bedrooms(soup)
        self.property_details["bathrooms"] = self.get_bathrooms(soup)
        self.property_details["size"] = self.get_size(soup)
        self.property_details["house_type"] = self.get_house_type(soup)
        self.property_details["address"] = self.get_address(soup)
        self.property_details["agent"] = self.get_agent(soup)
        self.property_details["description"] = self.get_description(soup)
        self.property_details["time_on_market"] = self.get_time_on_market(soup)
        self.property_details["features"] = self.get_features(soup)

    def get_images(self, soup):
        images = []
        gallery = soup.find("div", class_="gallery")
        if gallery:
            img_tags = gallery.find_all("img")
            for img_tag in img_tags:
                img_url = img_tag.get("data-src") or img_tag.get("src")
                if img_url:
                    images.append(img_url)
        return images

    def get_floorplans(self, soup):
        floorplans = []
        floorplan_section = soup.find("div", class_="floorplan")
        if floorplan_section:
            img_tags = floorplan_section.find_all("img")
            for img_tag in img_tags:
                img_url = img_tag.get("data-src") or img_tag.get("src")
                if img_url:
                    floorplans.append(img_url)
        return floorplans

    def get_price(self, soup):
        price_tag = soup.find("p", class_="price")
        if price_tag:
            return price_tag.get_text(strip=True)
        return None

    def get_bedrooms(self, soup):
        bedroom_tag = soup.find("span", class_="icon-bedroom")
        if bedroom_tag:
            return bedroom_tag.find_next_sibling("span").get_text(strip=True)
        return None

    def get_bathrooms(self, soup):
        bathroom_tag = soup.find("span", class_="icon-bathroom")
        if bathroom_tag:
            return bathroom_tag.find_next_sibling("span").get_text(strip=True)
        return None

    def get_size(self, soup):
        # OnTheMarket may not provide size directly
        # Implement logic if available
        return None

    def get_house_type(self, soup):
        type_tag = soup.find("h1", class_="main-heading")
        if type_tag:
            return type_tag.get_text(strip=True).split(" for ")[0]
        return None

    def get_address(self, soup):
        address_tag = soup.find("address", class_="property-address")
        if address_tag:
            return address_tag.get_text(strip=True)
        return None

    def get_agent(self, soup):
        agent_tag = soup.find("div", class_="agent-details")
        if agent_tag:
            agent_name = agent_tag.find("h3")
            if agent_name:
                return agent_name.get_text(strip=True)
        return None

    def get_description(self, soup):
        desc_tag = soup.find("div", class_="property-description")
        if desc_tag:
            return desc_tag.get_text(strip=True)
        return None

    def get_time_on_market(self, soup):
        time_tag = soup.find("p", class_="date-started")
        if time_tag:
            return time_tag.get_text(strip=True)
        return None

    def get_features(self, soup):
        features = []
        features_list = soup.find("ul", class_="property-features")
        if features_list:
            items = features_list.find_all("li")
            for item in items:
                features.append(item.get_text(strip=True))
        return features
