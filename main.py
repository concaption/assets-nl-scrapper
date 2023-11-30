#!/usr/bin/env python
"""
This script is used to test the Assets class.
"""
import time
from assets import Assets


EMAIL = "your_email"
PASSWORD = "your_password"

asset = Assets(headless=False)
driver, logged_in = asset.login(EMAIL, PASSWORD)
asset = Assets(headless=False, driver=driver)
if logged_in:
    time.sleep(5)
    driver = asset.fill_form(house_number="100", zipcode="1115CM", rental_income="400")
asset = Assets(headless=False, driver=driver)
time.sleep(5)
expected_price = asset.get_price()
print(expected_price)
