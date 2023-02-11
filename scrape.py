from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import config.urls as urls
import config.buttons as buttons
import config.partial_href_attributes as partial_href_attributes
from collections import defaultdict


from parse import parse


def scrape(driver: webdriver.Chrome):
    go_to_tms(driver)
    click_button_by_button_text(driver, buttons.quarter_button)

    data = defaultdict(list)

    click_button_by_button_text(driver, buttons.college_button)
    parse_all_colleges(driver, data)
    return data


def parse_all_colleges(driver: webdriver.Chrome, data: dict):
    college_buttons = driver.find_elements(
        By.CSS_SELECTOR, "a[href^='{}']".format(partial_href_attributes.colleges))

    for i in range(len(college_buttons)):
        college_buttons[i].click()
        parse(driver.page_source, data)
        driver.back()
        college_buttons = driver.find_elements(
            By.CSS_SELECTOR, "a[href^='{}']".format(partial_href_attributes.colleges))

    return data


def go_to_tms(driver: webdriver.Chrome) -> None:
    driver.get(urls.term_master_schedule)


def click_button_by_button_text(driver: webdriver.Chrome, button_text: str):
    driver.find_element(By.LINK_TEXT, button_text).click()
