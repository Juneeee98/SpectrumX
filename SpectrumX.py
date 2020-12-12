import selenium
import time
import io
import requests

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

import schedule
import time

# import from other py file
import functions as funct

# dot env file
import os
from dotenv import load_dotenv
load_dotenv()

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument("--test-type")
options = Options()
options.headless = False

driver = webdriver.Chrome(os.getenv("DRIVER_LOCATION"), chrome_options=options)
#driver = webdriver.Chrome(os.getenv("DRIVER_LOCATION"))


def login(driver):
    driver.get(os.getenv("WEBSITE"))
    n = True
    while n == True:
        if (os.getenv("LOGIN_SITE") in driver.current_url):
            username = driver.find_element_by_name('uname')
            password = driver.find_element_by_name('password')
            status = driver.find_element_by_name('domain')
            status.send_keys("Student")
            username.send_keys(os.getenv("USER"))
            password.send_keys(os.getenv("PASSWORD"))
            password.send_keys("\n")

        elif "You are not logged in." in driver.page_source:
            driver.get(os.getenv("WEBSITE"))

        elif "502 Bad Gateway" in driver.page_source:
            driver.close()
            time.sleep(60)

        elif "This site can’t be reached" in driver.page_source:
            driver.close()
            time.sleep(60)

        elif "course" not in driver.current_url in driver.page_source:
            n = False
    print("exit while loop")


def getFile(driver):
   count = 0
   for x in range(len(driver.find_elements_by_class_name("coursename"))):
      driver.find_elements_by_class_name("coursename")[x].click()
      for element in driver.find_elements_by_xpath('//div[1]/nav/ol/li[3]/a'):
         z = element.get_attribute("title")
      for element in driver.find_elements_by_xpath('//div/div/div[2]/div/a'):
         courseCode = z


         #print("course code= ", courseCode)
         # print(y[1])
         if 'resource' in element.get_attribute("href"):
            print(courseCode+ " " + element.get_attribute("text"))
            #dataCheck = compare(courseCode[1],element.get_attribute("text"))
            dataCheck = False
            # print("resource")
            if dataCheck == False:
               count+=1

         elif 'assign' in element.get_attribute("href"):
            print(courseCode + " " + element.get_attribute("text"))
            dataCheck = False
            #dataCheck = compare(courseCode[1],element.get_attribute("text"))
            if dataCheck == False:
               count+=1
               # print("assignment")
               
      driver.back()

def test(driver):
   count = 0
   for x in range(len(driver.find_elements_by_class_name("coursename"))):
      driver.find_elements_by_class_name("coursename")[x].click()
      for element in driver.find_elements_by_xpath('//div[1]/nav/ol/li[3]/a'):
         print("y=", element.get_attribute("title"))
               
      driver.back()


if __name__ == "__main__":
    login(driver)
    getFile(driver)
