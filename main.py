import bcolors
import json
import time
import os
import pickle
import requests
import random
import string
import base64
import threading
from random_word import RandomWords

from _utils import question, generate_phone_bearer
from termcolor import colored
from datetime import datetime
from json.decoder import JSONDecodeError
from seleniumwire.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import colorama

colorama.init()


# TODO - Generates phone verified discord accounts using set catchall or list of emails (different modes)
# TODO - Phone verification uses service textverified api here https://textverified.com/api
# TODO - Folder where user can put profile pictures for the bot to use (once one is used it is deleted and never used again)
# TODO - Once accounts are 100% they go into a text document inputted as email:password:discordtoken:discordname
# TODO - Program saves sessions and each discord can be opened in a chrome tab list for example:
# TODO - Opens discord Bot#0001 chrome tab straight to discord already logged in to https://discord.com/channels/@me
# TODO - Mass join discord would be a mode where the program listens and waits for the user to input a discord link. Once inputted it would join with as many accounts as it can.

class Account:

    def __init__(self, settings, email, task_number, proxy, phone_bearer):
        self.email = email

        # General
        self.task_number = task_number
        self.proxy = proxy
        self.session = requests.session()
        self.user_agent = self.generate_user_agent()

        # Account info
        self.username = self.generate_username()
        self.password = self.generate_password()
        self.discord_token = None
        self.session_cookies = None
        self.dob = self.generate_dob()

        # Chromedriver
        self.driver = None
        self.chrome_options = None
        self.headless = settings["headless_browser"]
        self.driver_cookies = None
        self.driver_proxy = proxy

        # Register
        self.capMonsterKey = settings["capMonster_api_key"]
        self.fingerprint = None
        self.super_properties = None

        # Verify
        self.phone_bearer = phone_bearer
        self.discord_targetId = "19"
        self.phone_verification_code = None
        self.phone = None

    def log(self, text, status):
        if status == 's':
            print(colored(
                f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] - [{self.email}] - [Discord Toolbox] - {text}",
                'green'))
        if status == 'f':
            print(colored(
                f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] - [{self.email}] - [Discord Toolbox] - {text}",
                'red'))
        if status == 'p':
            print(colored(
                f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] - [{self.email}] - [Discord Toolbox] - {text}",
                'cyan'))
        if status == 'd':
            print(colored(
                f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] - [{self.email}] - [Discord Toolbox] - {text}",
                'yellow'))
        if status == "S":
            print(
                bcolors.OK + f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] - [{self.email}] - [Discord Toolbox] - " + bcolors.OKMSG + f"{text}" + bcolors.ENDC)
        if status == "F":
            print(
                bcolors.ERR + f"[{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}] - [{self.email}] - [Discord Toolbox] - " + bcolors.ERRMSG + f"{text}" + bcolors.ENDC)

    def generate_username(self):
        self.log("Generating random username...", "p")
        random_word_gen = RandomWords()
        username = ""
        for usernamePart in range(2):
            username += random_word_gen.get_random_word().title()

        return username

    def generate_password(self):
        self.log("Generating random password...", "p")
        letters = string.ascii_lowercase
        result_str = ''.join(random.choice(letters) for i in range(8))
        return result_str

    def generate_dob(self):
        self.log("Generating DOB...", "p")
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        year = random.randint(1987, 2000)
        return f"{year}-{month}-{day}"

    def generate_user_agent(self):
        self.log("Finding random user agent...", "p")
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36"
        return user_agent

    def handle(self, _request):

        try:
            json_response = _request.json()
        except JSONDecodeError:
            json_response = "None Found"

        if _request.status_code == 200 or _request.status_code == 201:
            return True
        elif _request.status_code == 403:
            self.log(f"Access Denied. (Code 403)", "f")
        elif _request.status_code == 404:
            self.log(f"Failed to find page. (Code 404, Request URL: {_request.request.url}, Response: {json_response})",
                     "f")
        elif _request.status_code == 500:
            self.log(
                f"Internal Server Error. Request was done incorrectly. (Code: 500, Request URL: {_request.request.url}, Response: {json_response})",
                "f")
        else:
            response = f"Unknown error occurred. (Code: {_request.status_code}, Request URL: {_request.request.url}, Response: {json_response}"
            self.log(response, "f")

        exit(1)

    def get_captcha(self):
        s = requests.session()

        createTaskUrl = "https://api.capmonster.cloud/createTask"
        createTaskPayload = {
            "clientKey": self.capMonsterKey,
            "task":
                {
                    "type": "HCaptchaTaskProxyless",
                    "websiteURL": "https://discord.com/register",
                    "websiteKey": "4c672d35-0701-42b2-88c3-78380b0db560"
                }
        }
        createTask = s.post(createTaskUrl, json=createTaskPayload)
        taskId = createTask.json()["taskId"]

        getGRecapUrl = "https://api.capmonster.cloud/getTaskResult"
        getGRecapPayload = {
            "clientKey": self.capMonsterKey,
            "taskId": taskId
        }
        self.log("Waiting on captcha response...", "p")
        while True:
            time.sleep(2)
            getGRecap = s.post(getGRecapUrl, json=getGRecapPayload)
            captchaStatus = getGRecap.json()["status"]
            if captchaStatus == "processing":
                continue
            break
        self.log("Got response token!", "s")
        token = getGRecap.json()["solution"]["gRecaptchaResponse"]
        return token

    def proxy_config(self):
        (IPv4, Port, username, password) = self.proxy.split(':')

        ip = IPv4 + ':' + Port
        proxy_options = {
            "proxy": {
                "http": "http://" + username + ":" + password + "@" + ip,
                "https": "http://" + username + ":" + password + "@" + ip,
            }
        }
        self.driver_proxy = proxy_options
        self.proxy = proxy_options["proxy"]

    def set_arguments(self):
        opts = ChromeOptions()
        opts.add_argument('--allow-insecure-localhost')
        opts.add_argument('--ignore-ssl-errors')
        opts.add_argument('--ignore-certificate-errors-spki-list')
        opts.add_argument('--ignore-certificate-errors')
        opts.add_argument(f"user-agent={self.user_agent}")
        opts.add_argument("--disable-blink-features")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)
        opts.add_argument('--disable-extensions')
        opts.add_argument('disable-infobars')
        opts.add_argument('--window-size=500,645')
        opts.add_argument('--allow-profiles-outside-user-dir')
        opts.add_experimental_option('excludeSwitches', ['enable-logging'])
        if self.headless:
            opts.add_argument("--headless")
            opts.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        self.chrome_options = opts

    def save_account(self, session):

        with open("accounts.txt", "r") as f:
            lines = f.readlines()

        with open("accounts.txt", "w") as f:
            lines.append(f"{self.username}:{self.email}:{self.password}:{self.discord_token}\n")
            f.writelines(lines)

        self.log("Saved to accounts.txt", "s")

        if session:
            self.driver = None
            self.chrome_options = None
            with open("account_sessions.pickle", "rb") as f:
                account_sessions = pickle.load(f)
            account_sessions["accounts"][self.email] = self
            with open("account_sessions.pickle", "wb") as f:
                pickle.dump(account_sessions, f)
            self.log("Saved account instance.", "s")

    def create_driver(self):
        self.set_arguments()
        self.driver = Chrome(
            executable_path="chromedriver.exe",
            chrome_options=self.chrome_options,
            seleniumwire_options=self.driver_proxy
        )

    def replicate_driver_to_session(self):
        # Replicate chromedriver session
        self.log("Replicating driver to session...", "p")
        for cookie in self.driver_cookies:
            self.session.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"])

    def replicate_session_to_driver(self):
        # Replicate requests session
        self.log("Replicating session to driver...", "p")
        self.driver.delete_all_cookies()
        for cookie in self.session_cookies:
            self.driver.add_cookie({
                'name': cookie.name,
                'value': cookie.value,
                'domain': cookie.domain,
            })

    def create_registration(self):
        self.log("Opening browser...", "p")
        self.create_driver()
        self.log("Going to discord...", "p")
        self.driver.get(f"https://discord.com/register?email={self.email}")
        self.log("Entering details...", "p")
        username_element = self.driver.find_element(By.NAME, "username")
        password_element = self.driver.find_element(By.NAME, "password")

        username_element.send_keys(self.username)
        time.sleep(3)

        password_element.send_keys(self.password)

        # Month
        time.sleep(3)
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                  "November", "December"]
        self.driver.find_element(By.ID, "react-select-2-input").send_keys(months[int(self.dob.split("-")[1]) - 1])
        self.driver.find_element(By.ID, "react-select-2-input").send_keys(Keys.ENTER)

        # Day
        time.sleep(3)
        self.driver.find_element(By.ID, "react-select-3-input").send_keys(self.dob.split("-")[2])

        # Year
        time.sleep(3)
        self.driver.find_element(By.ID, "react-select-4-input").send_keys(self.dob.split("-")[0])

        time.sleep(3)
        self.log("Submitting registering info...", "p")
        self.driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div/form/div/div/div[5]/button").click()

        self.log("Waiting for register request...", "p")
        register_request = self.driver.wait_for_request(pat="/api/v9/auth/register", timeout=100)
        if register_request.response.status_code == 400:
            self.log("Denied entry due to hcaptcha. Collecting session info for resubmit...", "d")

            self.fingerprint = register_request.headers["x-fingerprint"]
            self.super_properties = register_request.headers["x-super-properties"]
            self.driver_cookies = self.driver.get_cookies()
            return False
        if register_request.response.status_code == 201:
            self.log("Successfully registered without challenge!", "S")
            self.discord_token = json.loads(register_request.response.body)["token"]
            return True
        if register_request.response.status_code == 429:
            self.log("Rate limited! Try again in a bit.", "F")
            exit(1)
        else:
            self.log(f"Unexpected error occurred. ({register_request.response.status_code})", "F")
            exit(1)

    def verify_phone(self):
        self.log("Verifying account via phone...", "p")

        text_verify_headers = {
            "Authorization" f"Bearer {self.phone_bearer}"
        }
        targetGET = self.session.get(f"https://www.textverified.com/api/Targets/{self.discord_targetId}",
                                     headers=text_verify_headers)
        self.handle(targetGET)
        text_status = targetGET.json()["status"]
        cost = targetGET.json()["cost"]
        if text_status != 4:
            self.log("Discord text verification api is down!", "F")
            exit(1)

        userGET = self.session.get("https://www.textverified.com/api/Users", headers=text_verify_headers)
        self.handle(userGET)
        user_balance = userGET.json()["credit_balance"]
        if cost > user_balance:
            self.log("Out of text verification currency!", "F")
            exit(1)

        self.log("Creating verification...", "p")
        # Create verification
        verificationPOST = self.session.post("https://www.textverified.com/api/Verifications",
                                             json={"id": self.discord_targetId}, headers=text_verify_headers)
        self.handle(verificationPOST)
        verification_id = verificationPOST.json()["id"]
        self.phone = verificationPOST.json()["number"]

        # TODO: SEND CODE VIA SELENIUM HERE

        ######

        # Check for text
        self.log("Waiting for code...", "p")
        while True:
            verificationGET = self.session.get(f"https://www.textverified.com/api/Verifications/{verification_id}",
                                               headers=text_verify_headers)
            self.log(verificationGET.json(), "d")
            verification_status = verificationGET.json()["status"]
            if verification_status == "Completed":
                break
        self.phone_verification_code = verificationPOST.json()["code"]

    def register(self):
        self.log(f"Starting register for {self.email}...", "p")
        registered = self.create_registration()
        if registered:
            self.save_account(session=False)
            return True

        self.replicate_driver_to_session()
        hcaptcha_token = self.get_captcha()
        self.log("Submitting registration...", "p")
        registerDATA = {
            "URL": "https://discord.com/api/v9/auth/register",
            "DATA": {
                "fingerprint": self.fingerprint,
                "email": self.email,
                "username": self.username,
                "password": self.password,
                "invite": None,
                "consent": True,
                "date_of_birth": self.dob,
                "gift_code_sku_id": None,
                "captcha_key": hcaptcha_token
            },
            "HEADERS": {
                "origin": "https://discord.com",
                "referer": f"https://discord.com/register?email={self.email}",
                "user-agent": self.user_agent,
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-fingerprint": self.fingerprint,
                "x-super-properties": self.super_properties
            }
        }
        registerPOST = self.session.post(registerDATA["URL"], json=registerDATA["DATA"],
                                         headers=registerDATA["HEADERS"], proxies=self.proxy)
        self.handle(registerPOST)
        self.discord_token = registerPOST.json()["token"]
        self.log("Successfully registered discord account.", "S")
        self.session_cookies = self.session.cookies
        self.save_account(session=True)
        # self.verify_phone()

    def create_login(self):
        if not self.driver:
            self.create_driver()
        # self.driver.get(f"https://discord.com/login?email={self.email}")
        self.driver.get(f"https://discord.com/")
        self.log(self.session_cookies, "p")
        self.replicate_session_to_driver()
        self.log(self.driver.get_cookies(), "p")
        self.driver.get(f"https://discord.com/channels/@me")
        time.sleep(10000)
        password_element = self.driver.find_element(By.NAME, "password")
        submit_element = self.driver.find_element(By.XPATH,
                                                  "/html/body/div[1]/div[2]/div/div/div/div/form/div/div/div[1]/div[2]/button[2]")

        password_element.send_keys(self.password)
        time.sleep(2)
        submit_element.click()

        login_request = self.driver.wait_for_request(pat="/api/v9/auth/login", timeout=100)
        if login_request.response.status_code == 400:
            self.log("Denied entry due to hcaptcha. Collecting session info for retry...", "d")
            self.driver_cookies = self.driver.get_cookies()
            return False
        if login_request.response.status_code == 200:
            self.log("Successfully logged in without challenge!", "S")
            self.driver_cookies = self.driver.get_cookies()
            return True

    def login(self):
        self.log("Logging in...", "p")
        login_success = self.create_login()
        if login_success:
            return True
        self.replicate_driver_to_session()
        hcaptcha_token = self.get_captcha()
        loginDATA = {
            "URL": "https://discord.com/api/v9/auth/login",
            "DATA": {
                "login": self.email,
                "password": self.password,
                "undelete": False,
                "captcha_key": hcaptcha_token,
                "login_source": None,
                "gift_code_sku_id": None
            },
            "HEADERS": {
                "origin": "https://discord.com",
                "referer": f"https://discord.com/login?email={self.email}",
                "user-agent": self.user_agent,
                "x-debug-options": "bugReporterEnabled",
                "x-discord-locale": "en-US",
                "x-fingerprint": self.fingerprint,
                "x-super-properties": self.super_properties
            }
        }
        loginPOST = self.session.post(loginDATA["URL"], json=loginDATA["DATA"], headers=loginDATA["HEADERS"],
                                      proxies=self.proxy)
        self.handle(loginPOST)
        self.log("Successfully logged in.", "S")
        self.session_cookies = self.session.cookies


class CLI:

    @staticmethod
    def menu():
        menu_answer = question("menu", "Main Menu", ["Generate accounts", "Open account", "Mass join discord"])

        if menu_answer == "Generate accounts":
            print("Generating accounts via emails...")

            # Emails
            with open("emails.txt", "r") as f:
                emails = [line.replace("\n", "") for line in f.readlines()]

            # Proxies
            with open("proxies.txt", "r") as f:
                proxies = [line.replace("\n", "") for line in f.readlines()]

            # Settings
            with open("settings.json", "r") as f:
                _settings = json.load(f)

            _phone_bearer = generate_phone_bearer()

            print("Preparation done.")
            for email in emails:
                print(email)
            input("The following emails are going to be used. Do you want to continue? ")

            proxy_num = 0
            for _task_number in range(len(emails)):
                if _task_number > len(proxies):
                    proxy_num = 0

                account = Account(_settings, emails[_task_number], _task_number, proxies[proxy_num], _phone_bearer)
                account.proxy_config()
                threading.Thread(target=account.register, args=()).start()

                proxy_num += 1

        if menu_answer == "Open account":
            with open("account_sessions.pickle", "rb") as f:
                accounts = pickle.load(f)["accounts"]
            accounts_list = [f"{email}" for email in accounts]
            if not accounts_list:
                cli.error("No accounts saved.")
            accounts_list.append("Go back.")

            account_prompt = question("account", "Choose an account",
                                      accounts_list)
            if account_prompt == "Go back.":
                cli.reset()
            chosen_account = accounts[account_prompt]
            chosen_account.login()

        if menu_answer == "Mass join discord":
            join_link = input("Please enter the discord join link: ")
            print("Joining with saved accounts...")

    @staticmethod
    def reset():
        cli.clear()
        cli.menu()

    @staticmethod
    def error(message):
        cli.clear()
        print(bcolors.FAIL + message + bcolors.ENDC)
        cli.menu()

    @staticmethod
    def clear():
        os.system("clear")


if __name__ == '__main__':
    cli = CLI()
    cli.menu()
