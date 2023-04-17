import os
import smtplib
import ssl
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium.common.exceptions import NoSuchElementException, \
    ElementNotInteractableException, ElementClickInterceptedException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import time
import datetime
from selenium import webdriver
import emailDistribution as distribution

# setting the URL for BeautifulSoup to operate in
url = "URL-TO-APOTHEKEN-PORTAL"

erstellte_passe = 0
sent_mails = 0
wrong_mails = []


def setup_driver():
    options = webdriver.ChromeOptions()
    os.chdir(os.getenv("DOWNLOAD_DIRECTORY"))
    prefs = {"profile.default_content_settings.popups": 0,
             "download.default_directory": os.getcwd() + os.path.sep,
             }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(executable_path=r'C:\Users\phili\Documents\impfpassKram\passGenerator\chromedriver.exe',
                              options=options)
    driver.maximize_window()
    driver.get(url)

    driver.find_element(By.NAME, 'email').send_keys("APOTHEKENPORTAL-EMAIL")
    input_password = driver.find_element(By.NAME, 'password')
    input_password.send_keys("APOTHEKENPORTAL-PASSWORD")
    input_password.submit()
    time.sleep(2)

    driver.find_element(By.NAME, 'email').send_keys("kiliandresse@aol.com")
    input_password = driver.find_element(By.NAME, 'password')
    input_password.send_keys("syqqes-qasnos-gyWpu0")
    input_password.submit()
    time.sleep(2)

    return driver


# creating a procedure to fill the form on the website of the APOTHEKENPORTAL
def fulfill_form(first, last, birth, vac, date, dose, genesen, driver):
    # use Chrome Dev Tools to find the names or IDs for the fields in the form
    new_birth = datetime.datetime.strptime(birth, '%d.%m.%y')
    if new_birth.year > 2014:
        new_birth = new_birth.replace(year=new_birth.year - 100)

    new_birth = new_birth.strftime('%d.%m.%Y')
    new_date = datetime.datetime.strptime(date, '%d.%m.%y').strftime('%d.%m.%Y')
    new_vac = vac

    # try to find the element for 30 seconds
    log_counter = 0
    while log_counter < 30:
        try:
            input_first = driver.find_element(By.NAME, 'firstName')
            break
        except NoSuchElementException:
            log_counter += 1
            time.sleep(1)
            pass

    if log_counter == 30:
        raise ValueError('Login was unsuccesful')

    # find the other elements for the form
    input_genesen = driver.find_element(By.XPATH, "//input[@type='checkbox']")
    input_last = driver.find_element(By.NAME, 'lastName')
    input_birthdate = driver.find_element(By.NAME, 'birthdate')
    input_vaccine = driver.find_element(By.NAME, 'vaccine')
    input_date = driver.find_element(By.NAME, 'vaccinationDate')
    input_dose = driver.find_element(By.NAME, 'doseNumber')

    # #input the values and hold a bit for the next action
    input_date.send_keys(new_date)
    time.sleep(0.1)
    input_first.send_keys(first)
    time.sleep(0.1)
    input_last.send_keys(last)
    time.sleep(0.1)
    input_birthdate.send_keys(new_birth)
    time.sleep(0.1)

    # if the person is already vaccinated, check the checkbox which needs to be done through ActionChains
    if genesen == 1:
        action = ActionChains(driver)
        action.move_to_element(input_genesen).click().perform()
        time.sleep(0.1)

    # if the person is vaccinated with Janssen, the name of the vaccine needs to be changed
    if vac.strip() == 'Janssen':
        new_vac = 'COVID-19 Vaccine Janssen'

    # if the person is vaccinated with Moderna, the name of the vaccine needs to be changed
    if vac.strip() == 'Moderna':
        new_vac = 'COVID-19 Vaccine Moderna'

    input_vaccine.send_keys(new_vac)

    dose_counter = 0

    # wait for the page to load and then send the dose number
    time.sleep(1)
    while dose_counter < 30:
        try:
            input_dose.send_keys(dose)
            break
        except ElementNotInteractableException:
            time.sleep(1)
            dose_counter += 1
            pass

    time.sleep(0.5)
    input_last.submit()
    time.sleep(1)
    seg_counter = 0
    while seg_counter < 30:
        try:
            # find the button to download the pdf
            download_pdf = driver.find_element(By.XPATH, '//button[normalize-space()="PDF herunterladen"]')
            break
        except NoSuchElementException:
            time.sleep(1)
            seg_counter += 1
            pass

    if seg_counter == 30:
        raise ValueError("Download page unable to reach")

    # try to click the button to download the pdf for 30 seconds
    download_counter = 0
    while download_counter < 30:
        try:
            download_pdf.click()
            break
        except ElementNotInteractableException:
            time.sleep(1)
            download_counter += 1
            pass
        except ElementClickInterceptedException:
            time.sleep(1)
            download_counter += 1
            pass

    if download_counter == 30:
        raise ValueError("Download unavailable")

    # wait for the pdf to be downloaded
    while not driver.find_element(By.XPATH, '//button[normalize-space()="QR-Code anzeigen"]').is_enabled():
        time.sleep(1)
    time.sleep(0.5)
    driver.get(url)
    time.sleep(1)


# creating a procedure to read the data from the csv file
# for the first vaccine
def read_erste(erste):
    erste = erste.strip()
    parts = erste.split(", ")
    parts[0] = datetime.datetime.strptime(parts[0], '%d.%m.%Y')
    parts[0] = parts[0].strftime('%d.%m.%y')
    if parts[1] == "Astra":
        parts[1] = "Vaxzevria"
    elif parts[1] == "Biontech":
        parts[1] = "Corminaty"
    elif parts[1] == "Moderna" or parts[1] == "Janssen":
        parts[1] = parts[1]
    else:
        raise ValueError(f"{parts[1]} is not a valid vaccine")
    return parts


# creating a loop to do the procedure for all rows in the dataframe.
# Clean up the data to fit the function fulfill_form
# Depending on the state of the data, the function fulfill_form will be called with different parameters and
# possibly multiple times for one person
# The function fulfill_form will create the pdf and download it
def start_process(mail, driver, dataframe):
    global erstellte_passe
    lastname: str
    birthday: str
    vaccine: str
    vac_date: str
    dosage: str
    receiver_mail: str
    erst_impfung: str
    zweit_impfung: str
    gender: str

    try:
        for index, row in dataframe.iterrows():
            firstname = row[1].strip()
            lastname = row[2].strip()
            birthday = row[3].strip()
            vaccine = row[13].strip()
            vac_date = row[12].strip()
            dosage = row[14]
            receiver_mail = row[16]
            erst_impfung = row[17]
            zweit_impfung = row[18]
            gender = row[0]
            beide = 0

            if receiver_mail == receiver_mail:
                if erst_impfung == erst_impfung:
                    erst_impfung = erst_impfung.strip()
                    if erst_impfung == "genesen":
                        fulfill_form(firstname,
                                     lastname,
                                     birthday,
                                     vaccine,
                                     vac_date,
                                     dosage,
                                     1,
                                     driver)
                        erstellte_passe += 1
                        beide = 0
                        if mail:
                            try_sending_mail(gender, firstname, lastname, receiver_mail, beide)
                        continue
                    parts = read_erste(erst_impfung)
                    fulfill_form(firstname,
                                 lastname,
                                 birthday,
                                 parts[1],
                                 parts[0],
                                 "1",
                                 0,
                                 driver)
                    erstellte_passe += 1
                    beide = 1
                if zweit_impfung == zweit_impfung:
                    zweit_impfung = zweit_impfung.strip()
                    if zweit_impfung == "Johnson":
                        fulfill_form(firstname,
                                     lastname,
                                     birthday,
                                     vaccine,
                                     vac_date,
                                     f"{dosage}/1",
                                     0,
                                     driver)
                        erstellte_passe += 1
                        beide = 0
                        if mail:
                            try_sending_mail(gender, firstname, lastname, receiver_mail, beide)
                        continue
                    parts = read_erste(zweit_impfung)

                    fulfill_form(firstname,
                                 lastname,
                                 birthday,
                                 parts[1],
                                 parts[0],
                                 "2",
                                 0,
                                 driver)
                    erstellte_passe += 1
                    beide = 2
                fulfill_form(firstname,
                             lastname,
                             birthday,
                             vaccine,
                             vac_date,
                             dosage,
                             0,
                             driver)
                erstellte_passe += 1
                if mail:
                    try_sending_mail(gender, firstname, lastname, receiver_mail, beide)
    except Exception as error:
        print(error)


# this function sends the mail to the patient with a pdf
def try_sending_mail(gender, first, last, mail, beide):
    global sent_mails
    global wrong_mails

    try:
        distribution.send_mail(distribution.createBody(gender, last, beide),
                               distribution.create_file_name(first, last),
                               mail,
                               beide)
        sent_mails += 1
    except smtplib.SMTPRecipientsRefused:
        wrong_mails.append(mail)
        time.sleep(5)
        pass


# this function sends a mail to the admin if the process was successful
def send_succes_mail():
    sender_email = "SENDER_MAIL"
    password = "PASSWORD"
    context = ssl.create_default_context()
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = "ADMIN_MAIL"
    message['Subject'] = "Datensatz wurde erfolgreich verschickt"

    mail_string = ""

    for mail in wrong_mails:
        mail_string += mail + "\n"

    message.attach(MIMEText("Es wurden " + str(
        erstellte_passe) + " Impfpässe erstellt\nDarauf wurden " + str(
        sent_mails) + " Mails verschickt. \nFolgende Adressen waren fehlerhaft: " + mail_string,
                            "plain"))

    text = message.as_string()

    with smtplib.SMTP_SSL("SMTP_SERVER", 465, context=context) as server:
        server.login(user=sender_email, password=password)
        server.sendmail(sender_email, "ADMIN_MAIL", text)


# fulfill_form('Max', 'Mustermann', '19.08.84', 'Comirnaty', '10.06.21', '1')
# print(readErste("28.05.2021, Astra"))

# this function starts the process
def start(mail, df):
    quarter = int(df.shape[0] / 4)
    print(quarter)
    df1 = df.iloc[:quarter]
    df2 = df.iloc[quarter:quarter * 2]
    df3 = df.iloc[quarter * 2:quarter * 3]
    df4 = df.iloc[quarter * 3:]

    start_threading(mail, df1, df2, df3, df4)


# four threads to speed up the process
def start_threading(mail, df1, df2, df3, df4):
    first_quarter = threading.Thread(target=start_thread, args=(mail, df1))
    first_quarter.start()
    second_quarter = threading.Thread(target=start_thread, args=(mail, df2))
    second_quarter.start()
    third_quarter = threading.Thread(target=start_thread, args=(mail, df3))
    third_quarter.start()
    fourth_quarter = threading.Thread(target=start_thread, args=(mail, df4))
    fourth_quarter.start()

    first_quarter.join()
    second_quarter.join()
    third_quarter.join()
    fourth_quarter.join()
    send_succes_mail()


# start the process for a thread with a new driver
def start_thread(mail, df):
    start_process(mail, setup_driver(), df)
