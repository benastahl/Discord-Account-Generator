from seleniumwire.webdriver import Chrome
import time

if __name__ == '__main__':
    proxy = "207.202.165.85:6360:Sl2PwDaCSx:Z3rjnU26X4"
    (IPv4, Port, username, password) = proxy.split(':')

    ip = IPv4 + ':' + Port
    proxy_options = {
        "proxy": {
            "http": "http://" + username + ":" + password + "@" + ip,
            "https": "http://" + username + ":" + password + "@" + ip,
        }
    }
    driver = Chrome(
        executable_path="chromedriver.exe", seleniumwire_options=proxy_options)
    driver.get("https://www.discord.com")
    time.sleep(1000)
