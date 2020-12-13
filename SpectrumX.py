import selenium
import time
import io
import requests
import firebase_admin
import schedule
import re

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from firebase_admin import credentials
from firebase_admin import firestore

# import from other py file
#import functions as funct

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
# driver = webdriver.Chrome(os.getenv("DRIVER_LOCATION"))

cred = credentials.Certificate(os.getenv("serviceAccountKey"))
firebase_admin.initialize_app(cred)
firestore_db = firestore.client()
toBePushData = []

# Global variable
login_status = True

# --------------------------------------------------------------------------------------------
# Log in to SPeCTRUM
# --------------------------------------------------------------------------------------------
def login(driver):
    driver.get(os.getenv("WEBSITE"))                                # Open URL
    n = True
    while n == True:
        # If the term "loginAllType" is in the URL opened
        if os.getenv("LOGIN_SITE") in driver.current_url:
            username = driver.find_element_by_name('uname')
            password = driver.find_element_by_name('password')
            status = driver.find_element_by_name('domain')
            status.send_keys("Student")
            username.send_keys(os.getenv("USER"))
            password.send_keys(os.getenv("PASSWORD"))
            password.send_keys("\n")                                # Equivalent to 'Enter' key
            print('Credentials inserted. ')

            # If login is unsuccessful (incorrect credentials or different status)
            if driver.find_elements_by_class_name("error"):
                global login_status
                login_status = False
                print('Incorrect credentials inserted.')
                n = False                                           # Exit while-loop

        # If login page is incorrect
        elif "You are not logged in." in driver.page_source:
            print('Login page is incorrect.')
            driver.get(os.getenv("WEBSITE"))                        # Open URL again

        # If SPeCTRUM is down
        elif "502 Bad Gateway" in driver.page_source:
            print('SPeCTRUM is currently inaccessible')
            driver.close()
            time.sleep(60)

        # If SPeCTRUM webpage cannot be reached 
        elif "This site can’t be reached" in driver.page_source:
            print('SPeCTRUM is currently inaccessible')
            driver.close()
            time.sleep(60)

        # If login to SPeCTRUM is successful
        elif "course" not in driver.current_url in driver.page_source:
            n = False                                               # Exit while-loop

    print("Function login ended")


# --------------------------------------------------------------------------------------------
# Log out of SPeCTRUM
# --------------------------------------------------------------------------------------------
def logout(driver):
    driver.find_elements_by_class_name("menubar")[0].click()                        # Click on the menu bar
    driver.find_elements_by_xpath('//*[@id="action-menu-1-menu"]/a[6]')[0].click()  # Click on the log out button 
    time.sleep(5)                                                                   # Wait for 5 seconds for the main page to load

    # If successfully go to SPeCTRUM official website
    if driver.current_url == os.getenv("OFFICIAL_SITE"):
        driver.quit()
        print('Logged out successfully')

# --------------------------------------------------------------------------------------------
# Obtaining files from SPeCTRUM
# --------------------------------------------------------------------------------------------
def getFile(driver):
    
    # Get the number of courses taken by the user
    for x in range(len(driver.find_elements_by_class_name("coursename"))): 

        # Click into each course link
        driver.find_elements_by_class_name("coursename")[x].click()
        
        # Getting the course titles and store into the database
        for element in driver.find_elements_by_xpath('//div[1]/nav/ol/li[3]/a'):  
            z = element.get_attribute("title")
            courseCode = z.split(' ',1)
            data = {'CourseName': courseCode[1], 'CourseCode': courseCode[0]}
         #firestore_db.collection(u'Course').document(courseCode[0]).set(data)

        # Getting the subtopic for each courses (e.g. Week 1 : MATLAB 01 Intro)
        for element in driver.find_elements_by_xpath('//div/div/div[2]/div/a'):   
            
            if 'resource' in element.get_attribute("href"):   
                tempdata = {'name' : element.get_attribute("text"),'link': element.get_attribute("href"), 'type': "resource" }
                toBePushData.append(tempdata)                                                                                 # Check if the clickable link is directed to a file type 
            
            # Check if the clickable link is directed to submission type: Assignment
            elif 'assign' in element.get_attribute("href"):                        
                tempdata = {'name' : element.get_attribute("text"),'link': element.get_attribute("href"), 'type': "assign" }  # Create teamp variable to hold name and type of subtopic
                ActionChains(driver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform()                     # Open a new tab 
                driver.switch_to.window(driver.window_handles[-1])                                                            # Change focus 
                td= []                                                                              
                x=0

                # Find the left column of submission page
                for element1 in driver.find_elements_by_xpath('//td[1]'):                                   
                    if("Submission status" in element1.text or "Due date" in element1.text ):
                        # Find the right column and add to dictionary to be pushed to the database
                        dic = {element1.text : driver.find_elements_by_xpath('//td[2]')[x].text}            
                        td.append(dic)                                                                      
                        tempdata.update(dic)
                

                    x=x+1
                toBePushData.append(tempdata)                                                                                 # Update the toBePushed data + submission info
                driver.close()                                                                                                # Close current tab and switch back focus to main page
                driver.switch_to.window(driver.window_handles[0])
        
        # Pushing all subtopic updates to database
        #firestore_db.collection(u'Course').document(courseCode[0]).update({"subTopic": toBePushData})   
        driver.back()


if __name__ == "__main__":
    login(driver)
    
    # If log in is successful, run the following functions
    if login_status == True:
        getFile(driver)
        logout(driver)
