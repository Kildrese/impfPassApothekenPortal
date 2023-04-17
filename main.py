import os
import time
from dotenv import load_dotenv
import handleMails
import impfpassGeneration as impf
import emailDistribution as distribution
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# This is the main file. It is used to start the program. It is also used to start the program in different modes.
# The modes are:
#   - y: Full run. This will generate the impfpass and send the mails.
#   - p: Partial run. This will only generate the impfpass.
#   - w: Watch for wrong mails. This will only watch for wrong mails.
#   - x: Mail run. This will only send the mails.
df = pd.read_csv(
    os.getenv("PATH_TO_CSV") + input("Dateiname: ") + '.csv',
    sep=';', skiprows=int(input("Skipped: ")))
fullrun = input("Fullrun? (y/m/p/w): ")
if fullrun == "y":
    impf.start(True, df)
    print("Procedure concluded")
    time.sleep(30)
    print("Watching for wrong mails")
    handleMails.check_wrong_mails(df)
elif fullrun == "p":
    impf.start(False, df)
elif fullrun == "w":
    print("Watching for wrong mails")
    handleMails.check_wrong_mails(df)
else:
    print("Es wurden " + str(distribution.create_mails(df)) + " verschickt.")
    print("Procedure concluded")
    time.sleep(30)
    print("Watching for wrong mails")
    handleMails.check_wrong_mails(df)
