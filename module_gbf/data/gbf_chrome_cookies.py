from browser_cookie3 import ChromiumBased
import requests
import json

class ChromeGBF(ChromiumBased):
    """Class for Google Chrome"""
    def __init__(self, cookie_file=None, domain_name="", key_file=None, profile_name="Default"):
        args = {
            'linux_cookies': [
                    '~/.config/google-chrome/'+profile_name+'/Cookies',
                    '~/.config/google-chrome-beta/'+profile_name+'/Cookies'
                ],
            'windows_cookies': [
                    {'env': 'APPDATA', 'path': '..\\Local\\Google\\Chrome\\User Data\\' + profile_name + '\\Cookies'},
                    {'env': 'LOCALAPPDATA', 'path': 'Google\\Chrome\\User Data\\' + profile_name + '\\Cookies'},
                    {'env': 'APPDATA', 'path': 'Google\\Chrome\\User Data\\' + profile_name + '\\Cookies'},
                    {'env': 'APPDATA', 'path': '..\\Local\\Google\\Chrome\\User Data\\' + profile_name + '\\Network\\Cookies'},
                    {'env': 'LOCALAPPDATA', 'path': 'Google\\Chrome\\User Data\\' + profile_name + '\\Network\\Cookies'},
                    {'env': 'APPDATA', 'path': 'Google\\Chrome\\User Data\\' + profile_name + '\\Network\\Cookies'}
                ],
            'osx_cookies': ['~/Library/Application Support/Google/Chrome/'+profile_name+'/Cookies'],
            'windows_keys': [
                    {'env': 'APPDATA', 'path': '..\\Local\\Google\\Chrome\\User Data\\Local State'},
                    {'env': 'LOCALAPPDATA', 'path': 'Google\\Chrome\\User Data\\Local State'},
                    {'env': 'APPDATA', 'path': 'Google\\Chrome\\User Data\\Local State'}
                ],
            'os_crypt_name': 'chrome',
            'osx_key_service': 'Chrome Safe Storage',
            'osx_key_user': 'Chrome'
        }

        key_file = "C:\\Users\\yueec\\AppData\\Local\\Google\\Chrome\\User Data\\Local State"

        super().__init__(browser='Chrome', cookie_file=cookie_file, domain_name=domain_name, key_file=key_file, **args)


def get_game_cookies_v2(profile_name="Default"):
    game_cookies = requests.cookies.RequestsCookieJar()

    with open('cookies.json', 'r') as f:
        cookies = json.load(f)
        for cookie in cookies:
            game_cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])

    # for host in ['game.granbluefantasy.jp', '.game.granbluefantasy.jp', '.mobage.jp']:
    #     cookies = ChromeGBF(domain_name=host, profile_name=profile_name).load()
    #     game_cookies.update(cookies)

    return game_cookies
