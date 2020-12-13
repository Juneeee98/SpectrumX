import selenium
import time
import io
import requests
import firebase_admin
import multiprocessing as mp

from firebase_admin import credentials
from firebase_admin import firestore
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from multiprocessing import Process

import schedule
import time
import re

# import from other py file
#import functions as funct

# dot env file
import os
from dotenv import load_dotenv

load_dotenv()
cred = credentials.Certificate(os.getenv("serviceAccountKey"))
firebase_admin.initialize_app(cred)
firestore_db = firestore.client()

# Global variable
login_status = True

# --------------------------------------------------------------------------------------------
# Log in to SPeCTRUM
# --------------------------------------------------------------------------------------------



def login(driver, Username, Pass):
    # If the term "loginAllType" is in the URL opened
    driver.get(os.getenv("WEBSITE")) # Open URL
    n = True
    while n == True:
        if (os.getenv("LOGIN_SITE") in driver.current_url):
            username = driver.find_element_by_name('uname')
            password = driver.find_element_by_name('password')
            status = driver.find_element_by_name('domain')
            status.send_keys("Student")
            username.send_keys(Username)
            password.send_keys(Pass)
            password.send_keys("\n")

        # If login page is incorrect
        elif "You are not logged in." in driver.page_source:
            driver.get(os.getenv("WEBSITE"))
        
        # If SPeCTRUM is down
        elif "502 Bad Gateway" in driver.page_source:
            driver.close()
            time.sleep(60)
        
        # If SPeCTRUM webpage cannot be reached 
        elif "This site can’t be reached" in driver.page_source:
            driver.close()
            time.sleep(60)
        
        # If login to SPeCTRUM is successful
        elif "course" not in driver.current_url in driver.page_source:
            n = False
    print("Function login ended")

# --------------------------------------------------------------------------------------------
# Obtaining files from SPeCTRUM
# --------------------------------------------------------------------------------------------
def getFile(driver):
    toBePushData = []
    # Get the number of courses taken by the user
    for x in range(len(driver.find_elements_by_class_name("coursename"))): #get the length of Courses Taken by users
    # Click into each course link
      driver.find_elements_by_class_name("coursename")[x].click()         #clicking each course link
    # Getting the course titles and store into the database
      for element in driver.find_elements_by_xpath('//div[1]/nav/ol/li[3]/a'):  #getting the title of courses clicked and create them in database
         z = element.get_attribute("title")
         courseCode = z.split(' ',1)
         data = {'CourseName': courseCode[1], 'CourseCode': courseCode[0]}
         #firestore_db.collection(u'Course').document(courseCode[0]).set(data)

      # Getting the subtopic for each courses (e.g. Week 1 : MATLAB 01 Intro)
      for element in driver.find_elements_by_xpath('//div/div/div[2]/div/a'):   #getting the subtopic for each courses ie. Week 1 : MATLAB 01 Intro
         
        # Check if the clickable link is directed to type: Files or resources
         if 'resource' in element.get_attribute("href"):   
            tempdata = {'name' : element.get_attribute("text"),'link': element.get_attribute("href"), 'type': "resource" }
            toBePushData.append(tempdata)                     #check if the clickable link is directed to a file type 
            
    
        # Check if the clickable link is directed to submission type: Assignment
         elif 'assign' in element.get_attribute("href"):                        #check if the clickable link is directed to a assignment submission type
            
            tempdata = {'name' : element.get_attribute("text"),'link': element.get_attribute("href"), 'type': "assign" } #create teamp variable to hold name and type of subtopic
            ActionChains(driver).key_down(Keys.CONTROL).click(element).key_up(Keys.CONTROL).perform() #open a new tab 
            driver.switch_to.window(driver.window_handles[-1])                                        #change focus 

            td= []                                                                              
            x=0

            # Find the left column of submission page
            for element1 in driver.find_elements_by_xpath('//td[1]'):                                   #find left column of submission page
                if("Submission status" in element1.text or "Due date" in element1.text ):

                    dic = {element1.text : driver.find_elements_by_xpath('//td[2]')[x].text}            #find right column and add to dictionary to be pushed to database
                    td.append(dic)                                                                      
                    tempdata.update(dic)
                

                x=x+1
            toBePushData.append(tempdata)                                                           #update the toBePushed data + submission info
            driver.close()                                                                          #close current tab and switch back focus to main page
            driver.switch_to.window(driver.window_handles[0])
            
      # Pushing all subtopic updates to database
      firestore_db.collection(u'Course').document(courseCode[0]).update({"subTopic": toBePushData})   #pushing all subtopic updates to database
 
      driver.back()
    driver.quit()

def browser():
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    options = Options()
    options.headless = False
    driver = webdriver.Chrome(os.getenv("DRIVER_LOCATION"), chrome_options=options)
    #driver = webdriver.Chrome(os.getenv("DRIVER_LOCATION"))
    return driver

def subprocess():
 
    while True: 
        print("listening to new user")
        
        # options = webdriver.ChromeOptions()
        # options.add_argument('--ignore-certificate-errors')
        # options.add_argument("--test-type")
        # options = Options()
        # options.headless = False
        # driver = webdriver.Chrome(os.getenv("DRIVER_LOCATION"), chrome_options=options)
        # #driver = webdriver.Chrome(os.getenv("DRIVER_LOCATION"))
        # time.sleep(1)
        # login(driver)
        # getFile(driver)
        # driver.quit()



  

if __name__ == "__main__":


    # driver = browser()
    # p = Process(target=subprocess, )
    # p.start()

    # login(driver)
    # getFile(driver)
    temp = []
    Users = firestore_db.collection(u'Users').stream()
    for user in Users:
        temp.append(user.to_dict())

    print(temp) 
    
    for i in temp:
        driver= browser()
        login(driver, i['Username'], i['Password'])
        driver.quit()
    