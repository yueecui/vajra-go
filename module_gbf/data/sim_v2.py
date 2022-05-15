import requests
import re
import time
import random
import requests.cookies
import json
from module_huiji.danteng_lib import log
from module_gbf.data.gbf_chrome_cookies import get_game_cookies_v2


GAME_HOST = 'http://game.granbluefantasy.jp'


# 获取2个有间隔的时间戳
def get_double_timestamp():
    timestamp_b = int(time.time() * 1000)
    timestamp_a = timestamp_b - random.randint(5000, 50000)
    return timestamp_a, timestamp_b


class GBFSim:
    def __init__(self, cfg, check_ver=True):
        self._cfg = cfg
        # self._cookies = self.__get_game_cookies()
        self._cookies = get_game_cookies_v2(self._cfg['SIM']['cookies_user'])
        self._version = None
        self._lang = 0
        self._is_login = False
        self._game_status = {
            'max_weapon': 0,
            'max_summon': 0,
        }
        if check_ver:
            self._is_login = self._login()

    def __get_game_cookies(self):
        profile_name = self._cfg['SIM']['cookies_user']

        # print('====================================================')
        # print('开始从Chrome中获取游戏登录用cookies')
        game_cookies = requests.cookies.RequestsCookieJar()
        for host in ['game.granbluefantasy.jp', '.game.granbluefantasy.jp', '.mobage.jp']:
            cookies = self.__get_chrome_cookies(host, profile=profile_name)
            # print('获取到 {} 域名下的cookies {} 条'.format(host, len(cookies)))
            for key, value in cookies.items():
                game_cookies.set(key, value, domain=host)
        return game_cookies

    # GET 请求
    def get(self, url, rtype='get_api', fix_param=True):
        result = {
            'status_code': 0
        }
        if fix_param:
            timestamp_a, timestamp_b = get_double_timestamp()
            url += '&' if url.find('?') > -1 else '?'
            url += f'_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        response = requests.get(url, cookies=self._cookies, headers=self._get_headers(rtype=rtype))
        result['status_code'] = response.status_code
        if response.status_code == 200:
            try:
                result['data'] = json.loads(response.text)
            except json.JSONDecodeError:
                result['text'] = response.text
        return result

    # POST 请求
    def post(self, url, rtype='post_api', data_text='', fix_param=True):
        result = {
            'status_code': 0
        }
        if fix_param:
            timestamp_a, timestamp_b = get_double_timestamp()
            url += '&' if url.find('?') > -1 else '?'
            url += f'_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        response = requests.post(url, cookies=self._cookies,
                                 headers=self._get_headers(rtype=rtype, data_text=data_text), data=data_text)
        result['status_code'] = response.status_code
        if response.status_code == 200:
            try:
                result['data'] = json.loads(response.text)
            except:
                result['text'] = response.text
        return result

    # 获取请求用的header
    def _get_headers(self, rtype='', data_text=''):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
            'Host': 'game.granbluefantasy.jp',
            'Origin': 'http://game.granbluefantasy.jp',
            'Referer': 'http://game.granbluefantasy.jp/',
            'User-Agent': self._cfg['SIM']['user_agent'],
        }
        if rtype == 'get_api':
            headers.update({
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'X-VERSION': str(self._version),
            })
        elif rtype == 'post_api':
            headers.update({
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'X-VERSION': str(self._version),
                'Content-Length': str(len(data_text)),
                'Content-Type': 'application/json',
            })

        return headers

    # 设置游戏语言
    # 1 日语
    # 2 英语
    def set_language(self, lang):
        if lang == self._lang:
            return 0
        result = self._set_language(lang)
        if result['status_code'] == 204:
            self._lang = lang
            return 1
        else:
            raise Exception('切换语言时出错：%s' % result['status_code'])

    def _set_language(self, lang=1):
        request_url = f'http://game.granbluefantasy.jp/setting/save'
        data = {
            "special_token": None,
            "language_type": lang,
        }
        data_text = json.dumps(data, separators=(',', ':'))
        return self.post(request_url, data_text=data_text)

    # 打开MYPAGE获取基本信息
    def _login(self):
        result = self.get(GAME_HOST, fix_param=False, rtype='')
        if result['status_code'] != 200:
            raise Exception('获取MYPAGE时出错！')
        mypage_html = result['text']
        # 查找游戏版本号
        find = re.findall(r'Game.version = "(\d+)";', mypage_html)
        if not find or len(find) == 0:
            raise Exception('没有找到游戏版本号，可能需要刷新登录状态')
        self._version = find[0]

        # 查找游戏当前语言
        find = re.findall(r'Game.lang = \'([^\']+)\';', mypage_html)
        if not find:
            log('【注意】没有找到游戏语言')
        else:
            if find[0] == 'ja':
                self._lang = 1
            elif find[0] == 'en':
                self._lang = 2
            else:
                self._lang = 0

        # 查找角色ID
        find = re.findall(r'Game.userId = (\d+);', mypage_html)
        if find:
            user_id = int(find[0])
        else:
            user_id = 0
        if user_id == 0:
            log('【注意】没有找到角色ID')
        else:
            log(f'使用ID为{user_id}的账号登录')
        self._user_id = user_id

        # 获取当前武器和召唤石数量
        # 从个人信息页获取图鉴数量上限
        profile_url = f'{GAME_HOST}/rest/profile/achievement/{self._user_id}'
        result = self.get(profile_url, rtype='get_api')
        profile_json = result['data']
        self._game_status = {
            'max_weapon': profile_json["archive"]["weapon_num"]["max"],
            'max_summon': profile_json["archive"]["summon_num"]["max"],
        }

    def get_user_id(self):
        return self._user_id


