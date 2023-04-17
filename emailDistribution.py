import smtplib
import ssl
from email.message import EmailMessage
import unidecode
import os

subject = "MAIL_SUBJECT"
sender_email = "SENDING_EMAIL"
password = "PASSWORD"

fileDirectory = os.getenv("DOWNLOAD_DIRECTORY")


# Sends the mail with the pdf file of the certificate to the receiver
def send_mail(main_body, file, receiver, beide):
    body = main_body
    receiver_email = receiver
    # Create a multipart message and set headers
    message = EmailMessage()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject

    message.set_content(body)
    file_suffix = file.split(".pdf")

    # Alters the file name for a potential of multiple pdfs in the mail
    # and then adds the files to the message as PDF attachments
    i = beide
    while 0 <= i:
        file: str
        if i > 0:
            file = file_suffix[0] + " (" + str(i) + ").pdf"
        else:
            file = file_suffix[0] + ".pdf"

        filename = f"{fileDirectory}{file}"

        # Open PDF file in binary mode
        with open(filename, 'rb') as pdf:
            pdf_data = pdf.read()

        message.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=file)
        i -= 1

    # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("INSERT SMTP SERVER", 465, context=context) as server:
        server.login(user=sender_email, password=password)
        server.send_message(message)
        print(file + " gesendet an: " + receiver_email)


# Creates the file name for the pdf file in the style of the APOTHEKENPORTAL
def create_file_name(first, last):
    filename = "Impfzertifikat_"

    unaccented_firstname = unidecode.unidecode(first)
    unaccented_lastname = unidecode.unidecode(last)

    filename += unaccented_firstname
    filename += "_"
    filename += unaccented_lastname + ".pdf"

    return filename


# Creates the body of the mail
def createBody(gender, last, beide):
    body = "Sehr geehrte"
    if gender == 1:
        body += "r Herr "
    else:
        body += " Frau "

    body += last
    body += ",\n" \
            "\n" \
            "wir hoffen, dass Sie Ihre Impfung gut vertragen haben.\n" \
            "\n" \
            "Anbei finden Sie den QR-Code für Ihren digitalen Impfpass. "

    if (beide == 1):
        body += "In dem PDF mit (1) am Ende befindet sich Ihr Zertifikat für die Zweitimpfung. " \
                "Im Anderen für Ihre Erstimpfung. "
    elif (beide == 2):
        body += "In dem PDF mit (1) am Ende befindet sich Ihr Zertifikat für die Zweitimpfung. " \
                "In dem PDF mit (2) am Ende Ihre Boosterimpfung und in dem letzte Ihre Erstimpfung. "
    body += "Falls die Datei nicht korrekt angezeigt wird (bspw. als Fragezeichen), " \
            "lässt sie sich trotzdem mit einem Doppelklick öffnen. " \
            "Laden Sie sich die CovPass App herunter und scannen Sie den QR-Code, " \
            "dann erhalten Sie den digitalen Nachweis Ihrer Impfung. \n" \
            "\n" \
            "Mit freundlichen Grüßen,\n" \
            "Ihr IMPFTEAM"
    return body


# Function to send mails to all receivers in the csv file
def create_mails(df):
    sent_mails = 0
    for index, row in df.iterrows():
        gender = row[0]
        firstname = row[1].strip()
        lastname = row[2].strip()
        mail_address = row[16]
        erst_imfpung = row[17]
        zweit_impfung = row[18]
        # print(createFileName(row[1], row[2]))
        beide = 0
        if mail_address == mail_address:
            if erst_imfpung == erst_imfpung:
                beide = 1
                if erst_imfpung.strip() == "genesen":
                    beide = 0
            if zweit_impfung == zweit_impfung:
                beide = 2
                if zweit_impfung.strip() == "Johnson":
                    beide = 0
                if not erst_imfpung == erst_imfpung:
                    beide = 1

            send_mail(createBody(gender, lastname, beide),
                      create_file_name(firstname, lastname),
                      mail_address,
                      beide)
            sent_mails += 1

    return sent_mails
