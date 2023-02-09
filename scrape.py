from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import config.urls as urls
import config.buttons as buttons

from parse import parse


def scrape(driver: webdriver.Chrome):
    go_to_tms(driver)
    click_button_by_button_text(driver, buttons.quarter_button)
    click_button_by_button_text(driver, buttons.college_button)
    click_button_by_button_text(driver, buttons.college_subject_button)
    data = parse(driver.page_source)
    return data


def go_to_tms(driver: webdriver.Chrome) -> None:
    driver.get(urls.term_master_schedule)


def click_button_by_button_text(driver: webdriver.Chrome, button_text: str):
    driver.find_element(By.LINK_TEXT, button_text).click()
