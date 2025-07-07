# trev wrote this script all by himself
# this takes a list of guessed file urls for doanload
import sys
import requests
import time

urls = [
    "https://www.irishimmigration.ie/wp-content/uploads/2025/05/SAVD-Decisions-07-January-to-13-January-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/01/SAVD-Decisions-14-January-to-20-January-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/01/SAVD-Decisions-21-January-to-27-January-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/02/SAVD-Decisions-28-January-to-03-February-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/02/SAVD-Decisions-04-February-to-10-February-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/02/SAVD-Decisions-11-February-to-17-February-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/02/SAVD-Decisions-18-February-to-24-February-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/02/SAVD-Decisions-25-February-to-03-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/03/SAVD-Decisions-04-March-to-10-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/03/SAVD-Decisions-11-March-to-17-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/03/SAVD-Decisions-18-March-to-24-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/03/SAVD-Decisions-25-March-to-31-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/04/SAVD-Decisions-01-April-to-07-April-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/04/SAVD-Decisions-08-April-to-14-April-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/04/SAVD-Decisions-15-April-to-21-April-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/04/SAVD-Decisions-22-April-to-28-April-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/04/SAVD-Decisions-29-April-to-05-May-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/05/SAVD-Decisions-06-May-to-12-May-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/05/SAVD-Decisions-13-May-to-19-May-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/06/SAVD-Decisions-20-May-to-26-May-2025.pdf"
]

urls = [
    "https://www.irishimmigration.ie/wp-content/uploads/2025/03/SAVD-Decisions-25-March-to-31-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/04/SAVD-Decisions-25-March-to-31-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/05/SAVD-Decisions-25-March-to-31-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/06/SAVD-Decisions-25-March-to-31-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/03/SAVD-Decisions-25-March-to-31-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/04/SAVD-Decisions-25-March-to-31-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/05/SAVD-Decisions-25-March-to-31-March-2025.pdf",
    "https://www.irishimmigration.ie/wp-content/uploads/2025/06/SAVD-Decisions-25-March-to-31-March-2025.pdf",
 
]
 
 

for i,url in enumerate(urls[:5]):
    print(i,url.split('/')[-1])
    try:
        req = requests.get(url)
        print (req)
    except:
        print ('does not exist - sorry!')
    time.sleep(1)


sys.exit()



x = requests.get('https://www.irishimmigration.ie/wp-content/uploads/2025/06/SAVD-Decisions-27-May-to-02-June-2025.pdf')
with open("trev.pdf","wb") as f:
    f.write(x.content)
    print ('content save to trev.pdf')