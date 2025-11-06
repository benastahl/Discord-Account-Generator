from PyInquirer import prompt
import json
import requests


def question(name, message, choices):
    questions = [
        {
            'type': "list",
            'name': name,
            'message': message,
            "choices": choices
        }
    ]
    answer = prompt(questions)[name]
    return answer


def generate_phone_bearer():
    with open("settings.json", "r") as f:
        settings = json.load(f)

    authenticationDATA = {
        "URL": "https://www.textverified.com/api/SimpleAuthentication",
        "HEADERS": {
            "X-SIMPLE-API-ACCESS-TOKEN": settings["simple_api_access_token"]
        }
    }
    authenticationGET = requests.session().post(authenticationDATA["URL"], headers=authenticationDATA["HEADERS"])
    if authenticationGET.status_code == 200:
        return authenticationGET.json()["bearer_token"]
    print("Failed to generate text verification api bearer token.")
    print(authenticationGET.status_code)
    exit(1)
