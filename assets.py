""" path: assets.py
author: @concaption
date: 2023-10-26
description: A python class to login to the assets.nl website and
    automatically fill in the form to create a new building.
    The bot will then extract the price of the building.
"""

import re
import time
import logging
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException


# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Assets:
    """
    Class for assets.nl bot
    
    Parameters
    ----------
    street : str
    """

    def __init__(self,
                 headless=True,
                 user_agent=None,
                 driver=None):
        self.url = "https://mijn.assets.nl/"
        if driver:
            self.driver = driver
        else:
            self.driver = self.set_driver(headless=headless, user_agent=user_agent)
        self.wait = WebDriverWait(self.driver, 10)

    def set_driver(self, headless, user_agent=None):
        """
        Set the Chrome driver
        
        Parameters
        ----------
        headless : bool
            Whether to run the Chrome driver in headless mode or not.
        """
        user_agents = [
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.53 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
            "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
        ]

        # select a random user agent if none is provided
        if not user_agent:
            user_agent = random.choice(user_agents)
            logger.info("Selected user agent: %s", user_agent)

        options = Options()
        if headless:
            options.add_argument("--headless")
            logger.info("Running Chrome in headless mode.")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--disable-gpu")
        options.add_argument('--disable-extensions')
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # logger.info("Setting up Chrome driver with options: %s", options.arguments)
        driver = webdriver.Chrome(options=options)
        logger.info("Chrome driver initialized successfully")
        return driver

    def login(self, email, password):
        """
        Go to the assets.nl login page and login

        Parameters
        ----------
        email : str
            The email address to use for login.
        password : str
            The password to use for login.

        Returns
        -------
        driver : selenium.webdriver.chrome.webdriver.WebDriver
            The Chrome driver object.
        login_status : bool
            Whether the login was successful or not.
        """
        login_status = False
        logger.info("Going to assets.nl website")
        login_url = "https://mijn.assets.nl/"
        self.driver.get(login_url)
        try:
            self.wait.until(EC.visibility_of_element_located((By.ID, 'username')))
            logger.info("Arrived at assets.nl website")
            email_input = self.driver.find_element(By.ID, 'username')
            password_input = self.driver.find_element(By.ID, 'password')
            email_input.send_keys(email)
            password_input.send_keys(password)
            submit_button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'c63db4457')))
            submit_button.click()
            login_status = True
        except TimeoutException:
            pass
        logger.info("Login: %s", login_status)
        return self.driver, login_status

    def fill_form(self, house_number="100", zipcode="1115CM", rental_income=None):
        """
        Fill in the form to create a new building

        Parameters
        ----------
        house_number : str
            The house number of the building.
        zipcode : st
            The zipcode of the building.
        rental_income : str
            The rental income of the building.
        
        Returns
        -------
        driver : selenium.webdriver.chrome.webdriver.WebDriver
            The Chrome driver object.
        """
        address = f"{house_number} {zipcode}"

        portfolio_card = self.driver.find_element(By.CLASS_NAME, 'icon-circle')
        portfolio_card.click()
        logger.info("Arrived at portfolio page")

        # Create new building
        new_building_button = self.driver.find_element(By.XPATH,
                                                       "//button[contains(., 'Nieuw pand')]")
        new_building_button.click()
        logger.info("Creating new building")
        time.sleep(1)

        # Input Address and select from autocomplete
        address_field = self.driver.find_element(By.XPATH,
                '//input[@placeholder="Voer het adres in op basis van straat of postcode"]')
        address_field.send_keys(address)

        first_autocomplete_option = self.wait.until(EC.visibility_of_element_located((By.XPATH,
                '//div[contains(@class, "mat-autocomplete-panel")]//mat-option[1]')))
        first_autocomplete_option.click()
        logger.info("Selected first address from autocomplete")

        # Question: "Wat is er op dit pand van toepassing?" (Owned)
        owned_radio = self.wait.until(EC.element_to_be_clickable((By.XPATH,
                "//mat-radio-button[contains(., 'Ik heb dit pand al in bezit')]")))
        owned_radio.click()

        # Question: "Wat ben je van plan met dit pand te doen?" (Rent)
        plan_rent_radio = self.wait.until(EC.element_to_be_clickable((By.XPATH,
                "//mat-radio-button[contains(., 'Ik wil dit pand verhuren')]")))
        plan_rent_radio.click()

        def select_radio_button_by_label(question_text, answer_text):
            xpath = f"//h3[contains(text(), '{question_text}')]/following-sibling::mat-radio-group//mat-radio-button//span[contains(text(), '{answer_text}')]"
            radio_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            radio_button.click()

        def enter_text_in_input_field(label_text, text):
            # XPath to find the input field associated with the given label
            xpath = f"//mat-label[contains(text(), '{label_text}')]/ancestor::mat-form-field//input"
            input_field = self.wait.until(EC.visibility_of_element_located((By.XPATH, xpath)))
            input_field.clear()
            input_field.send_keys(text)

        # Answering the questions
        select_radio_button_by_label("Heb je dit pand in de afgelopen 12 maanden gekocht?", "Nee")
        select_radio_button_by_label("Is dit pand reeds gefinancierd?", "Nee")
        select_radio_button_by_label("Is dit pand momenteel verhuurd?", "Ja")
        select_radio_button_by_label("Is dit pand al langer dan 12 maanden verhuurd?", "Ja")
        select_radio_button_by_label("Ben je van plan dit pand te veranderen / verbouwen?", "Nee")

        # Handling input fields
        enter_text_in_input_field("Huuropbrengst", rental_income)
        enter_text_in_input_field("Aantal mogelijke huurcontracten", "1")

        # Submit the form
        submit_button = self.driver.find_element(By.XPATH, "//button[contains(., 'Pand aanmaken')]")
        submit_button.click()
        logger.info("Submitted form")
        return self.driver

    def get_price(self):
        """
        Extract the price from the page

        Returns
        -------
        price : str
            The price of the building.
        """
        price_xpath = "//mat-card-title[contains(text(), 'Waarde in verhuurde staat')]/ancestor::mat-card//mat-panel-description[contains(., '€')]"
        price_element = self.wait.until(EC.visibility_of_element_located((By.XPATH, price_xpath)))
        price_text = price_element.text
        price = re.search(r"€\s*([\d.,]+)", price_text)
        if price:
            extracted_price = price.group(1)
        else:
            extracted_price = None
        logger.info("Extracted price: %s", extracted_price)
        return extracted_price
