import requests
from _utils import generate_phone_bearer

if __name__ == '__main__':
    s = requests.session()
    bearer = generate_phone_bearer()
    headers = {
        "Authorization": f"Bearer {bearer}"
    }
    targetsGET = s.get("https://www.textverified.com/api/targets", headers=headers)
    print(targetsGET.json())

