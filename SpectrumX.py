import selenium
import time
import io
import requests
import firebase_admin
import multiprocessing as mp
import pickle

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

def getFile(driver, Username):
    toBePushData = []
    notifications = []
    oldData = fetchOldData(Username)
    # Get the number of courses taken by the user
    for x in range(len(driver.find_elements_by_class_name("coursename"))): #get the length of Courses Taken by users
    # Click into each course link
      driver.find_elements_by_class_name("coursename")[x].click()         #clicking each course link
    # Getting the course titles and store into the database
      for element in driver.find_elements_by_xpath('//div[1]/nav/ol/li[3]/a'):  #getting the title of courses clicked and create them in database
         z = element.get_attribute("title")
         courseCode = z.split(' ',1)
         data = {'CourseName': courseCode[1], 'CourseCode': courseCode[0]}
         #firestore_db.collection(u'Users').document(Username).collection('Subjects').document(courseCode[0]).set(data)

      # Getting the subtopic for each courses (e.g. Week 1 : MATLAB 01 Intro)
      for element in driver.find_elements_by_xpath('//div/div/div[2]/div/a'):   #getting the subtopic for each courses ie. Week 1 : MATLAB 01 Intro
         
        # Check if the clickable link is directed to type: Files or resources
         if 'resource' in element.get_attribute("href"):   
            tempdata = {'name' : element.get_attribute("text"),'link': element.get_attribute("href"), 'type': "resource" }
            if tempdata['link'] not in oldData:
               notifications.append(z + "\n" + element.get_attribute("text") + " have been uploaded. \n"  + "Link: " + element.get_attribute("href"))
               firestore_db.collection(u'Users').document(Username).collection('Notifications').document('notification').update({"noti": notifications})
            toBePushData.append(tempdata)
               

    
        # Check if the clickable link is directed to submission type: Assignment
         elif 'assign' in element.get_attribute("href"):                        #check if the clickable link is directed to a assignment submission type
            
            tempdata = {'name' : element.get_attribute("text"),'link': element.get_attribute("href"), 'type': "assign" } #create teamp variable to hold name and type of subtopic
            if tempdata['link'] not in oldData:
                notifications.append(z + "\n" + "Assignment submission is open (" + element.get_attribute("text") + ") \n"  + "Link: " + element.get_attribute("href"))
                firestore_db.collection(u'Users').document(Username).collection('Notifications').document('notification').update({"noti": notifications})
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
      firestore_db.collection(u'Users').document(Username).collection('Subjects').document(courseCode[0]).update({"subTopic": toBePushData})   #pushing all subtopic updates to database
      toBePushData = []
 
      driver.back()
    driver.quit()

def firstRun(driver, Username):
    toBePushData = []
    firestore_db.collection(u'Users').document(Username).collection('Notifications').document('notification').set({"noti": toBePushData})
    # Get the number of courses taken by the user
    for x in range(len(driver.find_elements_by_class_name("coursename"))): #get the length of Courses Taken by users
    # Click into each course link
      driver.find_elements_by_class_name("coursename")[x].click()         #clicking each course link
    # Getting the course titles and store into the database
      for element in driver.find_elements_by_xpath('//div[1]/nav/ol/li[3]/a'):  #getting the title of courses clicked and create them in database
         z = element.get_attribute("title")
         courseCode = z.split(' ',1)
         data = {'CourseName': courseCode[1], 'CourseCode': courseCode[0]}
         firestore_db.collection(u'Users').document(Username).collection('Subjects').document(courseCode[0]).set(data)
       

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
      firestore_db.collection(u'Users').document(Username).collection('Subjects').document(courseCode[0]).update({"subTopic": toBePushData})   #pushing all subtopic updates to database
      toBePushData = []
      driver.back()
    driver.quit()

#create webdriver
def browser():  
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    options = Options()
    options.headless = False
    driver = webdriver.Chrome(os.getenv("DRIVER_LOCATION"), options=options)
    #driver = webdriver.Chrome(os.getenv("DRIVER_LOCATION"))
    return driver

#compare 2 list and return the differences
def returnNotMatches(a, b):
    return [[x for x in a if x not in b], [x for x in b if x not in a]]

#subprocess to check for new users to create new dataframe on database
def subprocess():
    try:
        pickle_in = open("Users.pickle", "rb") #open local pickle file that contains a record of previous user data
        Record = pickle.load(pickle_in)
        print(Record)

    except:
        pass 


    while True: 
        temp = []
        Users = firestore_db.collection(u'Users').stream() #get user data from database
        for user in Users:
            temp.append(user.to_dict())      
        with open("Users.pickle", "wb") as f:
             pickle.dump(temp,f)
  
        if returnNotMatches(temp, Record) == [[],[]]: #if no new user data
            print("no difference")
            # print(returnNotMatches(temp, Record))
        
        
        elif len(Record) > len(temp):                 #if some user data is deleted
            # print(returnNotMatches(temp, Record))
            Record = temp
            print("deleted")
            # print(returnNotMatches(temp, Record))

        else:                                         #if new user is added
            t = list(filter(None, returnNotMatches(temp, Record))) 
            print(t)
            newUsers = [item for sublist in t for item in sublist]
            print(newUsers)
            Record = temp
            print("setup first time")
            
            for newUser in newUsers:
                driver = browser()   
                login(driver, newUser['Username'],newUser['Password'])
                firstRun(driver,newUser['Username'])
        time.sleep(5)


def fetchOldData(Username):
    temp = []
    Files = firestore_db.collection(u'Users').document(Username).collection('Subjects').stream()
    for f in Files:
        temp.append(f.to_dict())
    
    t = temp
    k = []
    for i in t:
        k.append(i)
    
    q = []
    for i in k:
        q.append(i['subTopic'])
    
    flat_list = []
    for sublist in q:
        for item in sublist:
            flat_list.append(item)
    
    f = []

    for i in range(len(flat_list)):
        f.append(flat_list[i]['link'])
    
    return f


if __name__ == "__main__":

    # p = Process(target=subprocess, )
    # p.start()                            #start subprocess

    temp = []
    Users = firestore_db.collection(u'Users').stream()
    for user in Users:
        temp.append(user.to_dict())

    print(temp) 
    
    for i in temp:
        driver= browser()
        login(driver, i['Username'], i['Password'])
        getFile(driver, i['Username'])

