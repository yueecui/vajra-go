import requests
import re
import time
from danteng_lib import log, load_obj, save_obj
import os
import sqlite3
import win32crypt
import requests.cookies


class GBFSim:
    game_host = 'http://game.granbluefantasy.jp'

    def __init__(self, cfg):
        self._cfg = cfg
        self._cookies = get_game_cookies(cfg)
        self._user_id = self._get_user_id()

    @staticmethod
    def _get_headers():
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
            'Host': 'game.granbluefantasy.jp',
            'Referer': 'http://game.granbluefantasy.jp/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36',
        }

    def _get_user_id(self):
        find = re.findall(r'Game.userId = (\d+);', self._get(self.game_host))
        if find:
            user_id = int(find[0])
        else:
            user_id = 0
        if user_id == 0:
            log('【注意】没有找到角色ID')
        else:
            log(f'使用ID为{user_id}的账号登录')
        return user_id

    def get_user_id(self):
        return self._user_id

    # GET 请求
    def _get(self, url):
        response = requests.get(url, cookies=self._cookies, headers=self._get_headers())
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f'连接到<{url}>时出错，请检查')


def get_chrome_cookies(url, profile):
    cookie_file_path = os.path.join(os.environ['LOCALAPPDATA'], r'Google\Chrome\User Data\{}\Cookies'.format(profile))
    # print(cookie_file_path)
    conn = sqlite3.connect(cookie_file_path)
    ret_dict = {}
    rows = list(conn.execute("select name, encrypted_value from cookies where host_key = '{}'".format(url)))
    conn.close()
    for row in rows:
        ret = win32crypt.CryptUnprotectData(row[1], None, None, None, 0)
        ret_dict[row[0]] = ret[1].decode()
    return ret_dict


def get_game_cookies(cfg):
    profile_name = cfg['SETTING']['cookies_user']

    # print('====================================================')
    # print('开始从Chrome中获取游戏登录用cookies')
    game_cookies = requests.cookies.RequestsCookieJar()
    for host in ['game.granbluefantasy.jp', '.game.granbluefantasy.jp', '.mobage.jp']:
        cookies = get_chrome_cookies(host, profile=profile_name)
        # print('获取到 {} 域名下的cookies {} 条'.format(host, len(cookies)))
        for key, value in cookies.items():
            game_cookies.set(key, value, domain=host)

    # print('获取cookies成功')
    # print('====================================================')
    # print('')

    return game_cookies

