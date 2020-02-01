#!/usr/bin/env python3
# SPDX-License-Identifier: ISC
""" Download backup from remote pfsense host """

import re
import datetime
import os
import requests
from requests.exceptions import Timeout
from bs4 import BeautifulSoup
from dotenv import load_dotenv
#from requests.exceptions import Timeout

load_dotenv()

USER = os.getenv("USER")
PASS = os.getenv("PASS")
URL = os.getenv("URL")
FOLDER = os.getenv("FOLDER")

if USER is None or PASS is None or URL is None or FOLDER is None:
    print("Please set .env with USER, PASS and URL variables")
    print("Example:")
    print("  USER=admin")
    print("  PASS=password")
    print("  URL=http://192.168.1.1")
    print("  FOLDER=backups")
    exit()

PAGE = f"{URL}/diag_backup.php"

print(f"Performing backup on: {PAGE}")


def get_csrf(body):
    """ Retrieve CRSF token from html body """
    pattern = re.compile(r"var\s+csrfMagicToken\s+=\s+\"(.*?)\";")
    soup = BeautifulSoup(body, "html.parser")
    all_script = soup.find_all("script", {"src":False})
    for individual_script in all_script:
        all_value = individual_script.string
        if all_value:
            if "csrfMagicToken" in all_value:
                return pattern.search(all_value).group(1)
    return None

def write_backup(content):
    """ Writes raw response (xml document) to file """
    date = datetime.datetime.now().replace(microsecond=0).isoformat().replace(':', '-')
    if FOLDER is None:
        pathname = f"backup-{date}.xml"
    else:
        pathname = f"{FOLDER}/backup-{date}.xml"
    print(f"Writing to {pathname}")
    with open(pathname, "wb") as file_name:
        file_name.write(content)

def get_backup():
    """ Perform backup """
    client = requests.session()

    try:
        response = client.get(PAGE, timeout=20)
    except Timeout:
        print("Error getting initial CSRF token. Bailing out!")
        exit()

    csrf_token = get_csrf(response.content)
    print(f"Got CRSF token for login page: {csrf_token}")

    login_data = {"login": "Login", "usernamefld": USER, \
                    "passwordfld": PASS, "__csrf_magic": csrf_token}

    try:
        response = client.post(PAGE, data=login_data, timeout=20)
    except Timeout:
        print("Error login in. Bailing out!")
        exit()

    csrf_token = get_csrf(response.content)
    print(f"Got CRSF token for backup page: {csrf_token}")

    backup_data = {"download": "download", "donotbackuprrd": "yes", "__csrf_magic": csrf_token}

    try:
        response = client.post(PAGE, data=backup_data, timeout=20)
    except Timeout:
        print("Error downloading xml backup. Bailing out!")
        exit()
    xml_backup = response.content
    write_backup(xml_backup)


get_backup()
