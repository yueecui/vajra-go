import requests
import re
import time
import os
import random
import sqlite3
import win32crypt
import requests.cookies
import json
from danteng_lib import log, save_json, load_json_v37 as load_json
from config import *


GAME_HOST = 'http://game.granbluefantasy.jp'


class GBFSim:
    def __init__(self, cfg):
        self._cfg = cfg
        self._cookies = get_game_cookies(cfg)
        self._version = None
        self._game_db = {}
        self._login()

    # GET 请求
    def _get(self, url, rtype=''):
        response = requests.get(url, cookies=self._cookies, headers=self._get_headers(rtype=rtype))
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f'连接到<{url}>时出错，请检查')

    # POST 请求
    def _post(self, url, rtype='post_api', data_text=''):
        result = {
            'data': '',
            'status_code': 0
        }
        response = requests.post(url, cookies=self._cookies, headers=self._get_headers(rtype=rtype, data_text=data_text), data=data_text)
        result['status_code'] = response.status_code
        if response.status_code == 200:
            result['data'] = json.loads(response.text)

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36',
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

    # 初始化统计数据，能读取就读取，不能读取就生成
    def init_local_db(self):
        self._generate_weapon_stat()
        self._generate_summon_stat()

        game_db = self._game_db

        # 播报新数据信息
        new_msg = ''
        if game_db['weapon']['total'] > 0:
            if game_db['weapon']['total'] == game_db['new']["weapon"]:
                new_msg = '（无新增）'
            else:
                new_msg = '（本地差 %d 个）' % (game_db['new']["weapon"] - game_db['weapon']['total'])
        log(f'当前总武器数量：{game_db["new"]["weapon"]}{new_msg}')

        new_msg = ''
        if game_db['summon']['total'] > 0:
            if game_db['summon']['total'] == game_db['new']["summon"]:
                new_msg = '（无新增）'
            else:
                new_msg = '（本地差 %d 个）' % (game_db['new']["summon"] - game_db['summon']['total'])
        log(f'当前总召唤石数量：{game_db["new"]["summon"]}{new_msg}')

    # 将当前状态保存
    def _save_statistics(self):
        save_json(self._game_db, STATISTICS_JSON)

    # 获取当前数据记录中所有存有ID的数据数量
    # 主要要验证数据是否存在
    def _generate_weapon_stat(self):
        self._game_db['weapon'] = {
            'total': 0,
            'need_en': [],  # 旧数据中有缺失en数据的
            'record': {}
        }
        weapon_db = self._game_db['weapon']
        # 初始化数据存储
        for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
            type_id = str(type_id_int)
            weapon_db['record'][type_id] = {}
            for rarity_id_int in WEAPON_RARITY_ID_LIST:
                rarity_id = str(rarity_id_int)
                weapon_db['record'][type_id][rarity_id] = {
                    'max': -1,  # 最大ID，需要注意ID是从0开始的，所以max和count相等的时候，实际上是缺了1个的
                    'count': 0,
                    'miss': [],
                }

        # 从本地文件中检索
        data_base_jp_path = os.path.join(self._cfg['PATH']['data'], 'weapon', 'jp')
        if not os.path.exists(data_base_jp_path):
            return -1
        weapon_json_filename_list = os.listdir(data_base_jp_path)
        for filename in weapon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue

            weapon_info = get_weapon_info_from_filename(filename)
            self._weapon_db_add_item(weapon_info)

        # 整理缺失index
        for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
            type_id = str(type_id_int)
            for rarity_id_int in WEAPON_RARITY_ID_LIST:
                rarity_id = str(rarity_id_int)

                record_info = weapon_db['record'][type_id][rarity_id]
                miss_count = record_info['max'] + 1 - record_info['count']

                for index in range(0, record_info['max'] + 1):
                    if miss_count == 0:
                        break
                    weapon_id = get_weapon_id(type_id, rarity_id, index)
                    weapon_json_fullpath = os.path.join(data_base_jp_path, f'{weapon_id}.json')
                    if not (os.path.exists(weapon_json_fullpath) and os.path.getsize(weapon_json_fullpath) > 0):
                        record_info['miss'].append(index)
                        miss_count -= 1

    def _weapon_db_add_item(self, weapon_info):
        weapon_db = self._game_db['weapon']
        data_base_path = os.path.join(self._cfg['PATH']['data'], 'weapon')

        record_info = weapon_db['record'][str(weapon_info['type'])][str(weapon_info['rarity'])]
        record_info['count'] += 1
        weapon_db['total'] += 1

        if weapon_info['index'] > record_info['max']:
            record_info['max'] = weapon_info['index']

        # 检查英文版数据是否存在
        en_filename = f'{weapon_info["id"]}.json'
        en_fullpath = os.path.join(data_base_path, 'en', en_filename)
        if not (os.path.exists(en_fullpath) and os.path.getsize(en_fullpath) > 0):
            weapon_db['need_en'].append(weapon_info["id"])

    def _weapon_db_add_item_by_filename(self, item_filename):
        self._weapon_db_add_item(get_weapon_info_from_filename(item_filename))

    def _generate_summon_stat(self):
        self._game_db['summon'] = {
            'total': 0,
            'need_en': [],  # 旧数据中有缺失en数据的
            'record': {}
        }

    # 打开MYPAGE获取基本信息
    def _login(self):
        mypage_html = self._get(GAME_HOST)
        # 查找游戏版本号
        find = re.findall(r'Game.version = "(\d+)";', mypage_html)
        if not find:
            log('【注意】没有找到游戏版本号')
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
        timestamp_a, timestamp_b = get_double_timestamp()
        profile_url = f'{GAME_HOST}/rest/profile/achievement/{self._user_id}?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        profile_json = json.loads(self._get(profile_url, rtype='get_api'))
        self._game_db['new'] = {
            'weapon': profile_json["archive"]["weapon_num"]["max"],
            'summon': profile_json["archive"]["summon_num"]["max"],
        }

    def get_user_id(self):
        return self._user_id

    def set_language(self, lang):
        if lang == self._lang:
            return 0
        result = self._set_language(lang)
        if result['status_code'] == 204:
            self._lang = lang
            return 1
        else:
            raise Exception('切换语言时出错：%s' % result['status_code'])

    # 下载武器数据
    def download_weapon_data(self):
        # 切语言到日文
        self._download_new_weapon_data()
        if self._cfg['OPTION']['download_miss_weapon'] == 'yes':
            self._download_miss_weapon_data()
        # 下载需要的英文内容
        self._download_weapon_data_en()

    def _download_new_weapon_data(self):
        # 抓取日语游戏数据
        self.set_language(1)

        # 尝试获取的索引深度
        guess_index_times = {}  # 深入检查倍率，每种武器每种稀有度单独设置
        guess_index_config_by_rarity = {
            1: {
                'step': 1,
                'max_time': 2,
            },
            2: {
                'step': 1,
                'max_time': 2,
            },
            3: {
                'step': 2,
                'max_time': 5,
            },
            4: {
                'step': 10,
                'max_time': 5,
            },
        }  # 每深入一倍，多检查若干个武器ID

        weapon_db = self._game_db['weapon']
        guess_record = weapon_db['record']

        # 遍历所有武器和稀有度
        while True:
            if self._game_db['weapon']['total'] + int(self._cfg['SETTING']['miss_weapon_count']) == self._game_db['new']['weapon']:
                log('本地武器数据数量已经匹配最新数据数量')
                break

            has_query = False  # 本次循环是否有新的请求，如果没新请求就跳出

            for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
                type_id = str(type_id_int)
                if type_id not in guess_record:
                    guess_record[type_id] = {}
                if type_id_int not in guess_index_times:
                    guess_index_times[type_id_int] = {}
                for rarity_id_int in WEAPON_RARITY_ID_LIST:
                    rarity_config = guess_index_config_by_rarity[rarity_id_int]
                    if rarity_id_int not in guess_index_times[type_id_int]:
                        guess_index_times[type_id_int][rarity_id_int] = 1
                    else:
                        guess_index_times[type_id_int][rarity_id_int] += 1
                    if guess_index_times[type_id_int][rarity_id_int] > rarity_config['max_time']:
                        continue

                    rarity_id = str(rarity_id_int)
                    log('============================================')
                    log(f'= {weapon_name} 稀有度{rarity_id} 第{guess_index_times[type_id_int][rarity_id_int]}层循环')
                    log('============================================')

                    current_record = guess_record[type_id][rarity_id]  # 做一个引用方便后面写代码
                    temp_miss_list = []  # 超出部分的临时miss表，如果后面找到存在ID就把临时表推到正式表里

                    # 先尝试往后猜新数据（之后再尝试检查miss表）
                    guess_next = True
                    while guess_next:
                        guess_index_length_min = current_record['max'] + rarity_config['step'] * (guess_index_times[type_id_int][rarity_id_int] - 1) + 1
                        guess_index_length_max = current_record['max'] + rarity_config['step'] * guess_index_times[type_id_int][rarity_id_int] + 1
                        if guess_index_length_min == guess_index_length_max:
                            break

                        for guess_index in range(guess_index_length_min, guess_index_length_max):
                            has_query = True
                            result_code = self._try_download_weapon_info(type_id, rarity_id, guess_index)
                            if result_code in [0, 1]:
                                if guess_index > current_record['max']:
                                    current_record['max'] = guess_index
                                    guess_index_times[type_id_int][rarity_id_int] = 1
                                if len(temp_miss_list) > 0:
                                    current_record['miss'].extend(temp_miss_list)
                                    temp_miss_list.clear()
                                break
                            elif result_code == -1:
                                if guess_index > current_record['max']:
                                    temp_miss_list.append(guess_index)
                                else:
                                    current_record['miss'].append(guess_index)
                                if guess_index == guess_index_length_max - 1:
                                    guess_next = False

            if not has_query:
                break

    def _download_miss_weapon_data(self):
        log('============================================')
        log('= 尝试重新下载缺失编号')
        log('============================================')
        weapon_db = self._game_db['weapon']

        # 从缺失里尝试再抓取一遍
        for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
            type_id = str(type_id_int)
            for rarity_id_int in WEAPON_RARITY_ID_LIST:
                rarity_id = str(rarity_id_int)

                record_info = weapon_db['record'][type_id][rarity_id]

                for miss_id in record_info['miss']:
                    self._try_download_weapon_info(type_id, rarity_id, miss_id)

    def _download_weapon_data_en(self):
        self.set_language(2)

        log('============================================')
        log('= 下载英文版缺失数据')
        log('============================================')
        weapon_db = self._game_db['weapon']
        for weapon_id in weapon_db['need_en']:
            self._try_download_weapon_info_by_id(weapon_id, lang='en')

    def _try_download_weapon_info(self, type_id, rarity_id, weapon_id, lang='jp'):
        self._try_download_weapon_info_by_id(get_weapon_id(type_id, rarity_id, weapon_id), lang)

    def _try_download_weapon_info_by_id(self, weapon_id, lang='jp'):
        guess_filename = f'{weapon_id}.json'
        local_path = os.path.join(self._cfg['PATH']['data'], 'weapon', lang, guess_filename)
        # 本地已经存在，返回0
        if os.path.exists(local_path):
            return 0
        # 本地不存在，向服务器请求
        weapon_result = self._request_weapon_detail(weapon_id)
        # 服务器存在并保存返回1
        if weapon_result['status_code'] == 200:
            self._weapon_db_add_item_by_filename(guess_filename)
            save_json(weapon_result['data'], local_path)
            log('武器[%s] %s 数据保存完毕' % (weapon_id, weapon_result['data']['name']))
            return 1
        # 服务器不存在，返回-1
        elif weapon_result['status_code'] == 500:
            log('武器[%s] 数据不存在' % weapon_id)
            return -1

    def _request_weapon_detail(self, weapon_id):
        timestamp_a, timestamp_b = get_double_timestamp()
        request_url = f'http://game.granbluefantasy.jp/archive/weapon_detail?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        data = {
            "special_token": None,
            "user_id": self._user_id,
            "kind_name": "1",
            "attribute": "0",
            "event_id": None,
            "story_id": None,
            "weapon_id": str(weapon_id),
        }
        data_text = json.dumps(data, separators=(',', ':'))
        return self._post(request_url, data_text=data_text)

    # 设置游戏语言
    # 1 日语
    # 2 英语
    def _set_language(self, lang=1):
        timestamp_a, timestamp_b = get_double_timestamp()
        request_url = f'http://game.granbluefantasy.jp/setting/save?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        data = {
            "special_token": None,
            "language_type": lang,
        }
        data_text = json.dumps(data, separators=(',', ':'))
        return self._post(request_url, data_text=data_text)


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


# 获取2个有间隔的时间戳
def get_double_timestamp():
    timestamp_b = int(time.time() * 1000)
    timestamp_a = timestamp_b - random.randint(5000, 50000)
    return timestamp_a, timestamp_b


# 根据条件生成武器ID
def get_weapon_id(type_id, rarity_id, weapon_id):
    return '10%s0%s%03d00' % (rarity_id, type_id, weapon_id)


# 从文件名获取武器信息
def get_weapon_info_from_filename(filename):
    find = re.findall(r'((\d)0(\d)0(\d)(\d{3})00)\.json', filename)
    if not find:
        return None
    info_tuple = find[0]
    if info_tuple[1] != '1':
        return None
    return {
        'id': int(info_tuple[0]),
        'type': int(info_tuple[3]),
        'rarity': int(info_tuple[2]),
        'index': int(info_tuple[4]),
    }
