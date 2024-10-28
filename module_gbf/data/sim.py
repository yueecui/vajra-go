import requests
import re
import time
import os
import random
import requests.cookies
import json
from module_huiji.danteng_lib import log, save_json, load_json, read_file
from config import *
from module_gbf.data.gbf_chrome_cookies import get_game_cookies_v2
from config import SKIP_WEAPON_NOTE_ID_LIST_PATH, DATA_PATH

GAME_HOST = 'https://game.granbluefantasy.jp'


class GBFSim:
    def __init__(self, cfg, check_ver=True):
        self._cfg = cfg
        self._cookies = get_game_cookies_v2(self._cfg['SIM']['cookies_user'])
        self._version = None
        self._game_db = {}
        self._is_login = False
        if check_ver:
            self._is_login = True
            self._login()

        # 初始化本地数据
        self._init_local_db()
        requests.packages.urllib3.disable_warnings()
        self._save_statistics()  # 备份一个输出文件

    # GET 请求
    def _get(self, url, rtype=''):
        result = {
            'status_code': 0
        }
        response = requests.get(url, cookies=self._cookies, headers=self._get_headers(rtype=rtype))
        result['status_code'] = response.status_code
        if response.status_code == 200:
            try:
                result['data'] = json.loads(response.text)
            except:
                result['text'] = response.text
        return result

    # POST 请求
    def _post(self, url, rtype='post_api', data_text=''):
        result = {
            'status_code': 0
        }
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
            'Origin': 'https://game.granbluefantasy.jp',
            'Referer': 'https://game.granbluefantasy.jp/',
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

    # 初始化统计数据，能读取就读取，不能读取就生成
    def _init_local_db(self):
        self._generate_weapon_stat()
        self._generate_summon_stat()

        game_db = self._game_db

        # 播报新数据信息
        if self._is_login:
            new_msg = ''
            if game_db['weapon']['total'] > 0:
                total_count = game_db['weapon']['total'] + int(self._cfg['SIM']['miss_weapon_count'])
                if total_count == game_db['new']["weapon"]:
                    new_msg = '（无新增）'
                else:
                    new_msg = '（本地差 %d 个）' % (game_db['new']["weapon"] - total_count)
            log(f'当前总武器数量：{game_db["new"]["weapon"]}{new_msg}')

            new_msg = ''
            if game_db['summon']['total'] > 0:
                total_count = game_db['summon']['total'] + int(self._cfg['SIM']['miss_summon_count'])
                if total_count == game_db['new']["summon"]:
                    new_msg = '（无新增）'
                else:
                    new_msg = '（本地差 %d 个）' % (game_db['new']["summon"] - total_count)
            log(f'当前总召唤石数量：{game_db["new"]["summon"]}{new_msg}')

    # 将当前状态保存
    def _save_statistics(self):
        save_json(self._game_db, os.path.join(DATA_PATH, STATISTICS_JSON))

    # 设置游戏语言
    # 1 日语
    # 2 英语
    def _set_language(self, lang=1):
        timestamp_a, timestamp_b = get_double_timestamp()
        request_url = f'https://game.granbluefantasy.jp/setting/save?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        data = {
            "special_token": None,
            "language_type": lang,
        }
        data_text = json.dumps(data, separators=(',', ':'))
        return self._post(request_url, data_text=data_text)

    # 获取当前数据记录中所有存有ID的数据数量
    # 主要要验证数据是否存在
    def _generate_weapon_stat(self):
        self._game_db['weapon'] = {
            'total': 0,
            'record': {}
        }
        weapon_db = self._game_db['weapon']
        # 初始化数据存储
        for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
            type_id = str(type_id_int)
            weapon_db['record'][type_id] = {}
            for rarity_id_int in RARITY_ID_LIST:
                rarity_id = str(rarity_id_int)
                weapon_db['record'][type_id][rarity_id] = {
                    'max': -1,  # 最大ID，需要注意ID是从0开始的，所以max和count相等的时候，实际上是缺了1个的
                    'count': 0,
                    'miss': [],
                    'angel': False,
                }

        # 从本地文件中检索
        data_base_jp_path = get_local_path('weapon', 'shop')
        if not os.path.exists(data_base_jp_path):
            return -1
        weapon_json_filename_list = os.listdir(data_base_jp_path)
        for filename in weapon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue

            weapon_info = get_item_info_from_filename(filename)
            if weapon_info:
                self._weapon_db_add_item(weapon_info)

        # 整理缺失index
        for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
            if type_id_int == 99:
                continue
            type_id = str(type_id_int)
            for rarity_id_int in RARITY_ID_LIST:
                rarity_id = str(rarity_id_int)

                record_info = weapon_db['record'][type_id][rarity_id]
                miss_count = record_info['max'] + 1 - record_info['count']
                if record_info['angel']:
                    miss_count += 1

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

        record_info = weapon_db['record'][str(weapon_info['type'])][str(weapon_info['rarity'])]
        record_info['count'] += 1
        weapon_db['total'] += 1

        if weapon_info['index'] > record_info['max']:
            if weapon_info['index'] < 990:
                record_info['max'] = weapon_info['index']
            else:
                record_info['angel'] = True

        # 检查英文版数据是否存在
        # en_filename = f'{weapon_info["id"]}.json'
        # en_fullpath = os.path.join(data_base_path, 'en', en_filename)
        # if not (os.path.exists(en_fullpath) and os.path.getsize(en_fullpath) > 0):
        #     weapon_db['need_en'].append(weapon_info["id"])

    def _weapon_db_add_item_by_filename(self, item_filename):
        self._weapon_db_add_item(get_item_info_from_filename(item_filename))

    def _generate_summon_stat(self):
        self._game_db['summon'] = {
            'total': 0,
            'record': {}
        }

        summon_db = self._game_db['summon']
        # 初始化数据存储
        for rarity_id_int in RARITY_ID_LIST:
            rarity_id = str(rarity_id_int)
            summon_db['record'][rarity_id] = {
                'max': -1,  # 最大ID，需要注意ID是从0开始的，所以max和count相等的时候，实际上是缺了1个的
                'count': 0,
                'miss': [],
            }

        # 从本地文件中检索
        data_base_jp_path = get_local_path('summon', 'shop')
        if not os.path.exists(data_base_jp_path):
            return -1
        summon_json_filename_list = os.listdir(data_base_jp_path)
        for filename in summon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue

            summon_info = get_item_info_from_filename(filename)
            self._summon_db_add_item(summon_info)

        # 整理缺失index
        for rarity_id_int in RARITY_ID_LIST:
            rarity_id = str(rarity_id_int)

            record_info = summon_db['record'][rarity_id]
            miss_count = record_info['max'] + 1 - record_info['count']

            for index in range(0, record_info['max'] + 1):
                if miss_count == 0:
                    break
                weapon_id = get_summon_id(rarity_id, index)
                weapon_json_fullpath = os.path.join(data_base_jp_path, f'{weapon_id}.json')
                if not (os.path.exists(weapon_json_fullpath) and os.path.getsize(weapon_json_fullpath) > 0):
                    record_info['miss'].append(index)
                    miss_count -= 1

    def _summon_db_add_item(self, summon_info):
        summon_db = self._game_db['summon']

        record_info = summon_db['record'][str(summon_info['rarity'])]
        record_info['count'] += 1
        summon_db['total'] += 1

        if summon_info['index'] > record_info['max']:
            record_info['max'] = summon_info['index']

    def _summon_db_add_item_by_filename(self, item_filename):
        self._summon_db_add_item(get_item_info_from_filename(item_filename))

    # 打开MYPAGE获取基本信息
    def _login(self):
        result = self._get(GAME_HOST)
        if result['status_code'] != 200:
            raise Exception('获取MYPAGE时出错！')
        mypage_html = result['text']
        # 查找游戏版本号
        find = re.findall(r'"version": "(\d+)",', mypage_html)
        if not find or len(find) == 0:
            raise Exception('没有找到游戏版本号，可能需要刷新登录状态')
        self._version = find[0]

        # 查找游戏当前语言
        find = re.findall(r'"lang": "(\w+)",', mypage_html)
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
        find = re.findall(r'"userId": (\d+),', mypage_html)
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
        result = self._get(profile_url, rtype='get_api')
        profile_json = result['data']
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

    # 下载武器图鉴数据
    def download_weapon_data(self):
        self._download_new_weapon_data()
        if (self._game_db['weapon']['total'] + int(self._cfg['SIM']['miss_weapon_count']) < self._game_db['new'][
            'weapon']) and self._cfg['SIM']['download_miss_weapon'] == 'yes':
            self._download_miss_weapon_data()
        # 下载额外需要的数据（武器里只包括英文版数据）
        self._download_weapon_data_add()

    def _download_new_weapon_data(self):
        # 抓取日语游戏数据
        self.set_language(1)

        log('')
        log('============================================')
        log('= 查找新增武器')
        log('============================================')

        # 尝试获取的索引深度
        guess_index_times = {}  # 深入检查倍率，每种武器每种稀有度单独设置
        weapon_db = self._game_db['weapon']
        guess_record = weapon_db['record']

        # 遍历所有武器和稀有度
        while True:
            if self._game_db['weapon']['total'] + int(self._cfg['SIM']['miss_weapon_count']) == self._game_db['new'][
                'weapon']:
                log('本地武器数据数量已经匹配最新数据数量')
                break

            has_query = False  # 本次循环是否有新的请求，如果没新请求就跳出

            for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
                type_id = str(type_id_int)
                if type_id not in guess_record:
                    guess_record[type_id] = {}
                if type_id_int not in guess_index_times:
                    guess_index_times[type_id_int] = {}
                for rarity_id_int in RARITY_ID_LIST:
                    rarity_config = GUESS_CONFIG_BY_RARITY[rarity_id_int]
                    if rarity_id_int not in guess_index_times[type_id_int]:
                        guess_index_times[type_id_int][rarity_id_int] = 1
                    else:
                        guess_index_times[type_id_int][rarity_id_int] += 1
                    if guess_index_times[type_id_int][rarity_id_int] > rarity_config['max_time']:
                        continue

                    rarity_id = str(rarity_id_int)
                    # log('============================================')
                    # log(f'= {weapon_name} 稀有度{rarity_id} 第{guess_index_times[type_id_int][rarity_id_int]}层循环')
                    # log('============================================')

                    current_record = guess_record[type_id][rarity_id]  # 做一个引用方便后面写代码
                    temp_miss_list = []  # 超出部分的临时miss表，如果后面找到存在ID就把临时表推到正式表里

                    # 先尝试往后猜新数据（之后再尝试检查miss表）
                    guess_next = True
                    while guess_next:
                        guess_index_length_min = current_record['max'] + rarity_config['step'] * (
                                guess_index_times[type_id_int][rarity_id_int] - 1) + 1
                        guess_index_length_max = current_record['max'] + rarity_config['step'] * \
                                                 guess_index_times[type_id_int][rarity_id_int] + 1
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
        # 抓取日语游戏数据
        self.set_language(1)

        log('============================================')
        log('= 尝试重新下载缺失编号')
        log('============================================')
        weapon_db = self._game_db['weapon']

        # 从缺失里尝试再抓取一遍
        for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
            type_id = str(type_id_int)
            for rarity_id_int in RARITY_ID_LIST:
                rarity_id = str(rarity_id_int)

                record_info = weapon_db['record'][type_id][rarity_id]

                for miss_id in record_info['miss']:
                    self._try_download_weapon_info(type_id, rarity_id, miss_id)

    def _download_weapon_data_add(self):
        en_need_list = []
        shop_need_list = []
        # 从本地文件中检索
        data_base_jp_path = get_local_path('weapon', 'jp')
        if not os.path.exists(data_base_jp_path):
            return -1
        weapon_json_filename_list = os.listdir(data_base_jp_path)
        for filename in weapon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue

            weapon_info = get_item_info_from_filename(filename)
            # 需要的商店数据
            shop_filename = f'{weapon_info["id"]}.json'
            shop_fullpath = get_local_path('weapon', 'shop', shop_filename)
            if not (os.path.exists(shop_fullpath) and os.path.getsize(shop_fullpath) > 0):
                shop_need_list.append(weapon_info["id"])

            # 需要的英文版
            en_filename = f'{weapon_info["id"]}.json'
            en_fullpath = get_local_path('weapon', 'en', en_filename)
            if not (os.path.exists(en_fullpath) and os.path.getsize(en_fullpath) > 0):
                en_need_list.append(weapon_info["id"])

        log('')
        log('============================================')
        log('= 下载商店缺失数据')
        log('============================================')

        if len(shop_need_list) == 0:
            log('没有缺失的商店武器数据了')
        else:
            self.set_language(1)
            for weapon_id in shop_need_list:
                save_path = get_local_path('weapon', 'shop', f'{weapon_id}.json')
                if not os.path.exists(save_path):
                    self._try_download_weapon_shop_info_by_id(weapon_id, save_path)

        log('')
        log('============================================')
        log('= 下载英文版缺失数据')
        log('============================================')

        if len(en_need_list) == 0:
            log('没有缺失的英文版武器数据了')
        else:
            self.set_language(2)
            for weapon_id in en_need_list:
                self._try_download_weapon_info_by_id(weapon_id, lang='en')

    def _try_download_weapon_info(self, type_id, rarity_id, weapon_id, lang='jp'):
        return self._try_download_weapon_info_by_id(get_weapon_id(type_id, rarity_id, weapon_id), lang)

    def _try_download_weapon_info_by_id(self, weapon_id, lang='jp', reload=False):
        guess_filename = f'{weapon_id}.json'
        local_path = get_local_path('weapon', lang, guess_filename)
        # 本地已经存在，返回0
        if not reload and os.path.exists(local_path):
            return 0
        # 本地不存在，向服务器请求
        weapon_result = self._request_weapon_detail(weapon_id)
        # 服务器存在并保存返回1
        if weapon_result['status_code'] == 200:
            save_json(weapon_result['data'], local_path)
            if not reload:
                self._weapon_db_add_item_by_filename(guess_filename)
                log('武器[%s] %s 数据保存完毕' % (weapon_id, weapon_result['data']['name']))
            else:
                log('武器[%s] %s 数据更新完毕' % (weapon_id, weapon_result['data']['name']))
            return 1
        # 服务器不存在，返回-1
        elif weapon_result['status_code'] == 500:
            log('武器[%s] 数据不存在' % weapon_id)
            return -1

    def _request_weapon_detail(self, weapon_id):
        timestamp_a, timestamp_b = get_double_timestamp()
        request_url = f'https://game.granbluefantasy.jp/archive/weapon_detail?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        data = {
            "special_token": None,
            "user_id": self._user_id,
            "kind_name": "0",
            "attribute": "0",
            "event_id": None,
            "story_id": None,
            "weapon_id": str(weapon_id),
        }
        data_text = json.dumps(data, separators=(',', ':'))
        return self._post(request_url, data_text=data_text)

    # 重新下载武器数据
    def reload_weapon_data(self):
        # 先更新日文数据
        self.set_language(1)
        log('')
        log('============================================')
        log('= 重新下载所有武器数据【图鉴日文】')
        log('============================================')

        # 从本地文件中检索（只检索日文版的数据）
        data_base_jp_path = get_local_path('weapon', 'jp')
        if not os.path.exists(data_base_jp_path):
            return -1
        weapon_json_filename_list = os.listdir(data_base_jp_path)
        for filename in weapon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue
            weapon_info = get_item_info_from_filename(filename)

            self._try_download_weapon_info_by_id(weapon_info['id'], reload=True)

        # 更新商店版本数据
        log('')
        log('============================================')
        log('= 重新下载所有武器数据【商店日文】')
        log('============================================')

        for filename in weapon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue
            weapon_info = get_item_info_from_filename(filename)

            weapon_id = weapon_info['id']
            save_path = get_local_path('weapon', 'shop', f'{weapon_id}.json')
            self._try_download_weapon_shop_info_by_id(weapon_id, save_path)

        # 更新英文版数据
        log('')
        log('============================================')
        log('= 重新下载所有武器数据【图鉴英文】')
        log('============================================')

        self.set_language(2)
        for filename in weapon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue
            weapon_info = get_item_info_from_filename(filename)

            self._try_download_weapon_info_by_id(weapon_info['id'], lang='en', reload=True)

    # 下载召唤石数据
    def download_summon_data(self):
        # 下载日文召唤石数据
        self._download_new_summon_data()
        if (self._game_db['summon']['total'] + int(self._cfg['SIM']['miss_summon_count']) < self._game_db['new'][
            'summon']) and self._cfg['SIM']['download_miss_summon'] == 'yes':
            self._download_miss_summon_data()
        # 下载额外需要的数据（召唤石里包括英文版数据、满突数据和终突数据）
        self._download_summon_data_add()

    def _download_new_summon_data(self):
        # 抓取日语游戏数据
        self.set_language(1)

        log('')
        log('============================================')
        log('= 查找新增召唤石')
        log('============================================')

        # 尝试获取的索引深度
        guess_index_times = {}  # 深入检查倍率，每种稀有度单独设置
        summon_db = self._game_db['summon']
        guess_record = summon_db['record']

        # 遍历所有武器和稀有度
        while True:
            if self._game_db['summon']['total'] + int(self._cfg['SIM']['miss_summon_count']) == self._game_db['new'][
                'summon']:
                log('本地召唤石数据数量已经匹配最新数据数量')
                break

            has_query = False  # 本次循环是否有新的请求，如果没新请求就跳出

            for rarity_id_int in RARITY_ID_LIST:
                rarity_config = GUESS_CONFIG_BY_RARITY[rarity_id_int]
                if rarity_id_int not in guess_index_times:
                    guess_index_times[rarity_id_int] = 1
                else:
                    guess_index_times[rarity_id_int] += 1
                if guess_index_times[rarity_id_int] > rarity_config['max_time']:
                    continue

                rarity_id = str(rarity_id_int)
                # log('============================================')
                # log(f'= {weapon_name} 稀有度{rarity_id} 第{guess_index_times[type_id_int][rarity_id_int]}层循环')
                # log('============================================')

                current_record = guess_record[rarity_id]  # 做一个引用方便后面写代码
                temp_miss_list = []  # 超出部分的临时miss表，如果后面找到存在ID就把临时表推到正式表里

                # 先尝试往后猜新数据（之后再尝试检查miss表）
                guess_next = True
                while guess_next:
                    guess_index_length_min = current_record['max'] + rarity_config['step'] * (
                            guess_index_times[rarity_id_int] - 1) + 1
                    guess_index_length_max = current_record['max'] + rarity_config['step'] * guess_index_times[
                        rarity_id_int] + 1
                    if guess_index_length_min == guess_index_length_max:
                        break

                    for guess_index in range(guess_index_length_min, guess_index_length_max):
                        has_query = True
                        result_code = self._try_download_summon_info(rarity_id, guess_index)
                        if result_code in [0, 1]:
                            if guess_index > current_record['max']:
                                current_record['max'] = guess_index
                                guess_index_times[rarity_id_int] = 1
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

    def _download_miss_summon_data(self):
        log('============================================')
        log('= 尝试重新下载缺失编号的召唤石')
        log('============================================')
        summon_db = self._game_db['summon']

        # 从缺失里尝试再抓取一遍
        for rarity_id_int in RARITY_ID_LIST:
            rarity_id = str(rarity_id_int)

            record_info = summon_db['record'][rarity_id]

            for miss_id in record_info['miss']:
                self._try_download_summon_info(rarity_id, miss_id)

    def _download_summon_data_add(self):
        # 获取下当前可最终凸石头的列表
        final_uncap_list = self._get_summon_final_uncap_list()

        en_need_list = []
        uncap_need_list = []
        final_uncap_need_list = []
        # 从本地文件中检索
        data_base_jp_path = get_local_path('summon', 'jp')
        if not os.path.exists(data_base_jp_path):
            return -1
        summon_json_filename_list = os.listdir(data_base_jp_path)
        for filename in summon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue

            summon_info = get_item_info_from_filename(filename)
            summon_filename = f'{summon_info["id"]}.json'
            # 检查是否缺少英文数据
            en_fullpath = get_local_path('summon', 'en', summon_filename)
            if not (os.path.exists(en_fullpath) and os.path.getsize(en_fullpath) > 0):
                en_need_list.append(summon_info["id"])
            # 检查是否缺少满突数据
            uncap_fullpath = get_local_path('summon', 'uncap', summon_filename)
            if not (os.path.exists(uncap_fullpath) and os.path.getsize(uncap_fullpath) > 0):
                summon_json = load_json(os.path.join(data_base_jp_path, filename))
                if not summon_json['is_arcarum']:
                    uncap_need_list.append(summon_info["id"])
            # 检查是否缺少终突数据
            if str(summon_info['id']) in final_uncap_list:
                final_uncap_fullpath = get_local_path('summon', 'final_uncap', summon_filename)
                if not (os.path.exists(final_uncap_fullpath) and os.path.getsize(final_uncap_fullpath) > 0):
                    final_uncap_need_list.append(summon_info["id"])

        log('')
        log('============================================')
        log('= 下载英文版缺失数据')
        log('============================================')

        if len(en_need_list) == 0:
            log('没有缺失的英文版召唤石数据了')
        else:
            self.set_language(2)
            for summon_id in en_need_list:
                self._try_download_summon_info_by_id(summon_id, lang='en')

        log('')
        log('============================================')
        log('= 下载满突缺失数据')
        log('============================================')

        if len(uncap_need_list) == 0:
            log('没有缺失的满突召唤石数据了')
        else:
            self.set_language(1)
            for summon_id in uncap_need_list:
                self._try_download_summon_uncap_info_by_id(summon_id, 2)

        log('')
        log('============================================')
        log('= 下载终突缺失数据')
        log('============================================')

        if len(final_uncap_need_list) == 0:
            log('没有缺失的满突召唤石数据了')
        else:
            self.set_language(1)
            for summon_id in final_uncap_need_list:
                self._try_download_summon_uncap_info_by_id(summon_id, 3)

    def _try_download_summon_info(self, rarity_id, summon_id, lang='jp'):
        return self._try_download_summon_info_by_id(get_summon_id(rarity_id, summon_id), lang)

    def _try_download_summon_info_by_id(self, summon_id, lang='jp'):
        guess_filename = f'{summon_id}.json'
        local_path = get_local_path('summon', lang, guess_filename)
        # 本地已经存在，返回0
        if os.path.exists(local_path):
            return 0
        # 本地不存在，向服务器请求
        summon_result = self._request_summon_detail(summon_id)
        # 服务器存在并保存返回1
        if summon_result['status_code'] == 200:
            if 'redirect' in summon_result['data']:
                log('召唤石[%s] 数据返回为重定向到首页' % summon_id)
                return -1

            self._summon_db_add_item_by_filename(guess_filename)
            save_json(summon_result['data'], local_path)
            log('召唤石[%s] %s 数据保存完毕' % (summon_id, summon_result['data']['name']))
            return 1
        # 服务器不存在，返回-1
        elif summon_result['status_code'] == 500:
            log('召唤石[%s] 数据不存在' % summon_id)
            return -1

    def _request_summon_detail(self, summon_id):
        timestamp_a, timestamp_b = get_double_timestamp()
        request_url = f'https://game.granbluefantasy.jp/archive/summon_detail?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        data = {
            "special_token": None,
            "user_id": self._user_id,
            "kind_name": "0",
            "attribute": "0",
            "event_id": None,
            "story_id": None,
            "summon_id": str(summon_id),
        }
        data_text = json.dumps(data, separators=(',', ':'))
        return self._post(request_url, data_text=data_text)

    def _try_download_summon_uncap_info_by_id(self, summon_id, uncap_lv):
        summon_filename = f'{summon_id}.json'
        if uncap_lv == 2:
            local_path = get_local_path('summon', 'uncap', summon_filename)
        elif uncap_lv == 3:
            local_path = get_local_path('summon', 'final_uncap', summon_filename)
        else:
            raise Exception('错误的uncap level')
        # 本地已经存在，返回0
        if os.path.exists(local_path):
            return 0
        # 本地不存在，向服务器请求
        summon_result = self._request_summon_supporter(summon_id, uncap_lv)
        # 服务器存在并保存返回1
        if summon_result['status_code'] == 200:
            if 'redirect' in summon_result['data']:
                log('召唤石[%s] 数据返回为重定向到首页' % summon_id)
                return -1
            save_json(summon_result['data'], local_path)
            log('召唤石[%s] %s [突破%d]数据保存完毕' % (summon_id, summon_result['data']['master']['name'], uncap_lv))
            return 1
        # 服务器不存在，返回-1
        elif summon_result['status_code'] == 500:
            log('召唤石[%s] 数据不存在' % summon_id)
            return -1

    def _request_summon_supporter(self, summon_id, uncap_lv):
        timestamp_a, timestamp_b = get_double_timestamp()
        request_url = f'https://game.granbluefantasy.jp/summon/summon_supporter/{summon_id}/{uncap_lv}?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        return self._get(request_url, rtype='get_api')

    def _get_summon_final_uncap_list(self):
        final_uncap_list = []

        result = self._get_summon_final_uncap_list_by_page(1)
        final_uncap_list.extend(result['data']['list'])
        last_page_index = result['data']['last']
        for page_index in range(2, last_page_index + 1):
            result = self._get_summon_final_uncap_list_by_page(page_index)
            final_uncap_list.extend(result['data']['list'])

        final_uncap_id_list = []
        for uncap_item_info in final_uncap_list:
            if uncap_item_info['master']['id'] not in final_uncap_id_list:
                final_uncap_id_list.append(uncap_item_info['master']['id'])

        return final_uncap_id_list

    def _get_summon_final_uncap_list_by_page(self, page_index):
        timestamp_a, timestamp_b = get_double_timestamp()
        request_url = f'https://game.granbluefantasy.jp/summon/list_supporter/{page_index}?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        data = {
            "evolution_step": "3",
            "is_new": False,
            "special_token": None,
        }
        data_text = json.dumps(data, separators=(',', ':'))
        return self._post(request_url, data_text=data_text)

    ######################################################################
    # 从商店API获取的数据
    ######################################################################

    # 查找新的武器数据
    def check_new_weapon_data(self):
        # 抓取日语游戏数据
        self.set_language(1)

        log('')
        log('============================================')
        log('= 通过商店API查找新增武器')
        log('============================================')

        # 尝试获取的索引深度
        guess_index_times = {}  # 深入检查倍率，每种武器每种稀有度单独设置
        weapon_db = self._game_db['weapon']
        guess_record = weapon_db['record']

        # 遍历所有武器和稀有度
        while True:
            if self._game_db['weapon']['total'] + int(self._cfg['SIM']['miss_weapon_count']) == self._game_db['new'][
                'weapon']:
                log('本地武器数据数量已经匹配最新数据数量')
                break

            has_query = False  # 本次循环是否有新的请求，如果没新请求就跳出

            for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
                type_id = str(type_id_int)
                if type_id not in guess_record:
                    guess_record[type_id] = {}
                if type_id_int not in guess_index_times:
                    guess_index_times[type_id_int] = {}
                for rarity_id_int in RARITY_ID_LIST:
                    rarity_config = GUESS_CONFIG_BY_RARITY[rarity_id_int]
                    if rarity_id_int not in guess_index_times[type_id_int]:
                        guess_index_times[type_id_int][rarity_id_int] = 1
                    else:
                        guess_index_times[type_id_int][rarity_id_int] += 1
                    if guess_index_times[type_id_int][rarity_id_int] > rarity_config['max_time']:
                        continue

                    rarity_id = str(rarity_id_int)
                    # log('============================================')
                    # log(f'= {weapon_name} 稀有度{rarity_id} 第{guess_index_times[type_id_int][rarity_id_int]}层循环')
                    # log('============================================')

                    current_record = guess_record[type_id][rarity_id]  # 做一个引用方便后面写代码
                    temp_miss_list = []  # 超出部分的临时miss表，如果后面找到存在ID就把临时表推到正式表里

                    # 先尝试往后猜新数据（之后再尝试检查miss表）
                    guess_next = True
                    while guess_next:
                        guess_index_length_min = current_record['max'] + rarity_config['step'] * (
                                guess_index_times[type_id_int][rarity_id_int] - 1) + 1
                        guess_index_length_max = current_record['max'] + rarity_config['step'] * \
                                                 guess_index_times[type_id_int][rarity_id_int] + 1
                        if guess_index_length_min == guess_index_length_max:
                            break

                        for guess_index in range(guess_index_length_min, guess_index_length_max):
                            has_query = True

                            weapon_id = get_weapon_id(type_id, rarity_id, guess_index)
                            save_path = get_local_path('weapon', 'shop', f'{weapon_id}.json')
                            if os.path.exists(save_path):
                                continue

                            result_code = self._try_download_weapon_shop_info_by_id(weapon_id, save_path)
                            if result_code == 1:
                                self._weapon_db_add_item_by_filename(get_weapon_id(type_id, rarity_id, guess_index))
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

    # 检查MISS武器
    def check_miss_weapon_data(self):
        # 抓取日语游戏数据
        self.set_language(1)

        log('')
        log('============================================')
        log('= 通过商店API检查缺失武器编号')
        log('============================================')
        weapon_db = self._game_db['weapon']

        # 从缺失里尝试再抓取一遍
        for type_id_int, weapon_name in WEAPON_TYPE_MAP.items():
            type_id = str(type_id_int)
            for rarity_id_int in RARITY_ID_LIST:
                rarity_id = str(rarity_id_int)

                record_info = weapon_db['record'][type_id][rarity_id]

                for miss_id in record_info['miss']:
                    weapon_id = get_weapon_id(type_id, rarity_id, miss_id)
                    save_path = get_local_path('weapon', 'shop', f'{weapon_id}.json')
                    if not os.path.exists(save_path):
                        self._try_download_weapon_shop_info_by_id(weapon_id, save_path)

    def _try_download_weapon_shop_info_by_id(self, weapon_id, save_path):
        # 本地不存在，向服务器请求
        weapon_result = self._request_shop_detail(weapon_id, 1)
        # 服务器存在并保存返回1
        if weapon_result['status_code'] == 200:
            if weapon_result['data']['data']['id']:
                save_json(weapon_result['data'], save_path)
                log('【商店】武器[%s] %s 数据保存完毕' % (weapon_id, weapon_result['data']['data']['name']))
                return weapon_result['data']
            else:
                log('【商店】武器[%s] 数据不存在' % weapon_id)
                return -1
        # 服务器不存在，返回-1
        elif weapon_result['status_code'] == 500:
            log('【商店】武器[%s] 数据不存在' % weapon_id)
            return -1

    def _try_download_weapon_note_info_by_id(self, weapon_id, save_path):
        # 本地不存在，向服务器请求
        weapon_result = self._request_weapon_note(weapon_id)
        # 服务器存在并保存返回1
        if weapon_result['status_code'] == 200:
            if weapon_result['data']:
                save_json(weapon_result, save_path)
                log('【图鉴】武器[%s] %s 数据保存完毕' % (weapon_id, weapon_result['data']['name']))
                return weapon_result['data']
            else:
                log('【图鉴】武器[%s] 数据不存在' % weapon_id)
                return -1
        # 服务器不存在，返回-1
        elif weapon_result['status_code'] == 500:
            log('【图鉴】武器[%s] 数据不存在' % weapon_id)
            return -1

    def _request_shop_detail(self, item_id, item_kind):
        timestamp_a, timestamp_b = get_double_timestamp()
        request_url = f'https://game.granbluefantasy.jp/result/detail?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        data = {
            "special_token": None,
            "item_id": str(item_id),
            "item_kind": str(item_kind),
        }
        data_text = json.dumps(data, separators=(',', ':'))
        return self._post(request_url, data_text=data_text)

    def _request_weapon_note(self, weapon_id):
        timestamp_a, timestamp_b = get_double_timestamp()
        request_url = f'https://game.granbluefantasy.jp/archive/weapon_detail?_={timestamp_a}&t={timestamp_b}&uid={self._user_id}'
        data = {
            "attribute": "0",
            "event_id": None,
            "kind_name": str(int(str(weapon_id)[4])+1),
            "special_token": None,
            "story_id": None,
            "user_id": str(self._user_id),
            "weapon_id": str(weapon_id),
        }
        data_text = json.dumps(data, separators=(',', ':'))
        return self._post(request_url, data_text=data_text)


    # 检查新增召唤石
    def check_new_summon_data(self):
        # 抓取日语游戏数据
        self.set_language(1)

        log('')
        log('============================================')
        log('= 通过商店API查找新增召唤石')
        log('============================================')

        # 尝试获取的索引深度
        guess_index_times = {}  # 深入检查倍率，每种稀有度单独设置
        summon_db = self._game_db['summon']
        guess_record = summon_db['record']

        # 遍历所有武器和稀有度
        while True:
            if self._game_db['summon']['total'] + int(self._cfg['SIM']['miss_summon_count']) == self._game_db['new'][
                'summon']:
                log('本地召唤石数据数量已经匹配最新数据数量')
                break

            has_query = False  # 本次循环是否有新的请求，如果没新请求就跳出

            for rarity_id_int in RARITY_ID_LIST:
                rarity_config = GUESS_CONFIG_BY_RARITY[rarity_id_int]
                if rarity_id_int not in guess_index_times:
                    guess_index_times[rarity_id_int] = 1
                else:
                    guess_index_times[rarity_id_int] += 1
                if guess_index_times[rarity_id_int] > rarity_config['max_time']:
                    continue

                rarity_id = str(rarity_id_int)
                # log('============================================')
                # log(f'= {weapon_name} 稀有度{rarity_id} 第{guess_index_times[type_id_int][rarity_id_int]}层循环')
                # log('============================================')

                current_record = guess_record[rarity_id]  # 做一个引用方便后面写代码
                temp_miss_list = []  # 超出部分的临时miss表，如果后面找到存在ID就把临时表推到正式表里

                # 先尝试往后猜新数据（之后再尝试检查miss表）
                guess_next = True
                while guess_next:
                    guess_index_length_min = current_record['max'] + rarity_config['step'] * (
                            guess_index_times[rarity_id_int] - 1) + 1
                    guess_index_length_max = current_record['max'] + rarity_config['step'] * guess_index_times[
                        rarity_id_int] + 1
                    if guess_index_length_min == guess_index_length_max:
                        break

                    for guess_index in range(guess_index_length_min, guess_index_length_max):
                        has_query = True
                        result_code = self._try_download_summon_shop_info(rarity_id, guess_index)
                        if result_code == 1:
                            self._summon_db_add_item_by_filename(get_summon_id(rarity_id, guess_index))
                        if result_code in [0, 1]:
                            if guess_index > current_record['max']:
                                current_record['max'] = guess_index
                                guess_index_times[rarity_id_int] = 1
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

    # 检查召唤石
    def check_miss_summon_data(self):
        # 抓取日语游戏数据
        self.set_language(1)

        log('')
        log('============================================')
        log('= 通过商店API检查缺失召唤石编号')
        log('============================================')
        summon_db = self._game_db['summon']

        # 从缺失里尝试再抓取一遍
        for rarity_id_int in RARITY_ID_LIST:
            rarity_id = str(rarity_id_int)

            record_info = summon_db['record'][rarity_id]

            for miss_id in record_info['miss']:
                self._try_download_summon_shop_info(rarity_id, miss_id)

    def _try_download_summon_shop_info(self, rarity_id, summon_id, reload=False):
        return self._try_download_summon_shop_info_by_id(get_summon_id(rarity_id, summon_id))

    def _try_download_summon_shop_info_by_id(self, summon_id, reload=False):
        guess_filename = f'{summon_id}.json'
        bak_local_path = get_local_path('summon', 'shop', guess_filename)
        miss_local_path = os.path.join(DATA_PATH, 'shop_miss', guess_filename)
        # 本地已经存在，返回0
        if not reload and os.path.exists(bak_local_path):
            return 0
        # 本地不存在，向服务器请求
        weapon_result = self._request_shop_detail(summon_id, 2)
        # 服务器存在并保存返回1
        if weapon_result['status_code'] == 200:
            if weapon_result['data']['data']['id']:
                if not reload:
                    save_json(weapon_result['data'], miss_local_path)
                save_json(weapon_result['data'], bak_local_path)
                log('【商店】召唤石[%s] %s 数据保存完毕' % (summon_id, weapon_result['data']['data']['name']))
                return 1
            else:
                log('【商店】召唤石[%s] 数据不存在' % summon_id)
                return -1
        # 服务器不存在，返回-1
        elif weapon_result['status_code'] == 500:
            log('【商店】召唤石[%s] 数据不存在' % summon_id)
            return -1

    # 根据从商店API跑出的数据下载新数据
    def download_data_by_new_id(self):
        check_new_id_path = os.path.join(DATA_PATH, 'check_new_id')
        check_new_id_list = os.listdir(check_new_id_path)

        if len(check_new_id_list) == 0:
            return

        # 抓取日语游戏数据
        self.set_language(1)

        log('============================================')
        log('= 尝试通过商店API跑出来的新数据')
        log('============================================')

        # 从缺失里尝试再抓取一遍
        for filename in check_new_id_list:
            item_info = get_item_info_from_filename(filename)
            if item_info['kind'] == 1:
                pass
                # self._try_download_weapon_info(item_info['type'], item_info['rarity'], item_info['index'])
            elif item_info['kind'] == 2:
                self._try_download_summon_info(item_info['rarity'], item_info['index'])

    # 获取所有召唤石ID
    def all_summon(self):
        for rarity_id in RARITY_ID_LIST:
            rarity_data = self._game_db['summon']['record'][str(rarity_id)]
            for summon_id in range(0, rarity_data['max'] + 1):
                if summon_id in rarity_data['miss']:
                    continue
                yield get_summon_id(rarity_id, summon_id)

    # 获取所有武器ID
    def all_weapon(self):
        for type_id in WEAPON_TYPE_MAP.keys():
            for rarity_id in RARITY_ID_LIST:
                rarity_data = self._game_db['weapon']['record'][str(type_id)][str(rarity_id)]
                for weapon_id in range(0, rarity_data['max'] + 1):
                    if weapon_id in rarity_data['miss']:
                        continue
                    yield get_weapon_id(type_id, rarity_id, weapon_id)
                if rarity_data['angel']:
                    yield get_weapon_id(type_id, rarity_id, 990)

    # 下载武器数据（第二版）
    # 只根据日文武器数据，下载英文shop数据
    def download_weapon_data_v2(self):
        shop_need_list = []
        # 从本地文件中检索
        data_base_jp_path = get_local_path('weapon', 'shop')
        if not os.path.exists(data_base_jp_path):
            return -1
        weapon_json_filename_list = os.listdir(data_base_jp_path)
        for filename in weapon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue

            weapon_info = get_item_info_from_filename(filename)
            # 需要的商店数据
            shop_filename = f'{weapon_info["id"]}.json'
            shop_fullpath = get_local_path('weapon', 'shop_en', shop_filename)
            if not (os.path.exists(shop_fullpath) and os.path.getsize(shop_fullpath) > 0):
                shop_need_list.append(weapon_info["id"])

        log('')
        log('============================================')
        log('= 下载英文商店缺失数据')
        log('============================================')

        if len(shop_need_list) == 0:
            log('没有缺失的英文商店武器数据了')
        else:
            # 切换下载英文数据
            self.set_language(2)
            for weapon_id in shop_need_list:
                save_path = get_local_path('weapon', 'shop_en', f'{weapon_id}.json')
                if not os.path.exists(save_path):
                    self._try_download_weapon_shop_info_by_id(weapon_id, save_path)

    # 下载武器图鉴数据
    # 2022年7月23日
    def get_skip_weapon_note_id_list(self):
        content, result = read_file(SKIP_WEAPON_NOTE_ID_LIST_PATH)
        if not result:
            return []
        else:
            raw_list = content.split('\n')
            skip_id_list = []
            for skip_id_text in raw_list:
                skip_id_text = skip_id_text.strip()
                if skip_id_text == '':
                    continue
                if skip_id_text[0:1] == '#':
                    continue
                try:
                    skip_id_list.append(f'{skip_id_text}.json')
                except ValueError:
                    continue
            return skip_id_list

    # 根据商店数据，补充下载图鉴数据
    def download_weapon_data_v2_note(self):
        shop_need_list = []
        # 从本地文件中检索
        data_base_jp_path = get_local_path('weapon', 'shop')
        if not os.path.exists(data_base_jp_path):
            return -1
        skip_id_list = self.get_skip_weapon_note_id_list()
        weapon_json_filename_list = os.listdir(data_base_jp_path)
        for filename in weapon_json_filename_list:
            if filename in skip_id_list:
                continue
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue

            weapon_info = get_item_info_from_filename(filename)
            # 需要的商店数据
            shop_filename = f'{weapon_info["id"]}.json'
            shop_fullpath = get_local_path('weapon', 'note', shop_filename)
            if not (os.path.exists(shop_fullpath) and os.path.getsize(shop_fullpath) > 0):
                shop_need_list.append(weapon_info["id"])

        log('')
        log('============================================')
        log('= 下载日文图鉴缺失数据')
        log('============================================')

        if len(shop_need_list) == 0:
            log('没有缺失的日文图鉴数据了')
        else:
            # 切换下载英文数据
            self.set_language(1)
            for weapon_id in shop_need_list:
                save_path = get_local_path('weapon', 'note', f'{weapon_id}.json')
                if not os.path.exists(save_path):
                    self._try_download_weapon_note_info_by_id(weapon_id, save_path)

    # 下载召唤石数据（第二版）
    # 从编成数据里抓取
    def download_summon_data_v2(self):
        # 获取下当前可最终凸石头的列表
        final_uncap_list = self._get_summon_final_uncap_list()
        skip_summon_id_list = get_skip_summon_id_list()

        en_need_list = []
        uncap_need_list = []
        final_uncap_need_list = []
        # 从本地文件中检索
        data_base_jp_path = get_local_path('summon', 'shop')
        if not os.path.exists(data_base_jp_path):
            return -1
        summon_json_filename_list = os.listdir(data_base_jp_path)
        for filename in summon_json_filename_list:
            full_path = os.path.join(data_base_jp_path, filename)
            if os.path.getsize(full_path) == 0:
                continue

            summon_info = get_item_info_from_filename(filename)
            if summon_info['id'] in skip_summon_id_list:
                continue

            summon_filename = f'{summon_info["id"]}.json'
            # 检查是否缺少满突数据
            uncap_fullpath = get_local_path('summon', 'uncap', summon_filename)
            if not (os.path.exists(uncap_fullpath) and os.path.getsize(uncap_fullpath) > 0):
                uncap_need_list.append(summon_info["id"])
            # 检查是否缺少终突数据
            if str(summon_info['id']) in final_uncap_list:
                final_uncap_fullpath = get_local_path('summon', 'final_uncap', summon_filename)
                if not (os.path.exists(final_uncap_fullpath) and os.path.getsize(final_uncap_fullpath) > 0):
                    final_uncap_need_list.append(summon_info["id"])

        log('')
        log('============================================')
        log('= 下载满突缺失数据')
        log('============================================')

        if len(uncap_need_list) == 0:
            log('没有缺失的满突召唤石数据了')
        else:
            self.set_language(1)
            for summon_id in uncap_need_list:
                self._try_download_summon_uncap_info_by_id(summon_id, 2)

        log('')
        log('============================================')
        log('= 下载终突缺失数据')
        log('============================================')

        if len(final_uncap_need_list) == 0:
            log('没有缺失的满突召唤石数据了')
        else:
            self.set_language(1)
            for summon_id in final_uncap_need_list:
                self._try_download_summon_uncap_info_by_id(summon_id, 3)

    # 获取所有新闻
    def download_all_news(self):
        # TODO
        pass


# 获取2个有间隔的时间戳
def get_double_timestamp():
    timestamp_b = int(time.time() * 1000)
    timestamp_a = timestamp_b - random.randint(5000, 50000)
    return timestamp_a, timestamp_b


# 根据条件生成武器ID
# 1位 - 固定为1，表示武器
# 2位 - 固定为0
# 3位 - 表示稀有度：N=1，R=2，SR=3，SSR=4
# 4-5位 - 武器类型
# 6-8位 - 类型内索引，从0开始
# 9-10位 - 固定为0
def get_weapon_id(type_id, rarity_id, weapon_id):
    return '10%s%02d%03d00' % (rarity_id, int(type_id), weapon_id)


# 根据条件生成召唤ID
# 召唤石ID规则
# 1位 - 固定为2，表示召唤石
# 2位 - 固定为0
# 3位 - 表示稀有度：N=1，R=2，SR=3，SSR=4
# 4位 - 固定为0
# 5-7位 - 稀有度内索引
# 8-10位 - 固定为0
def get_summon_id(rarity_id, summon_id):
    return '20%s0%03d000' % (rarity_id, summon_id)


# 从文件名获取ITEM信息
def get_item_info_from_filename(filename):
    filename = str(filename)
    if filename == '':
        return None
    # 武器
    if filename[0] == '1':
        find = re.findall(r'(\d0(\d)(\d{2})(\d{3})00)\.?(:?json)?', filename)
        if not find:
            return None
        info_tuple = find[0]
        return {
            'id': int(info_tuple[0]),
            'type': int(info_tuple[2]),
            'rarity': int(info_tuple[1]),
            'index': int(info_tuple[3]),
            'kind': 1,
        }
    # 召唤石
    elif filename[0] == '2':
        find = re.findall(r'(\d0(\d)0(\d{3})000)\.?(?:json)?', filename)
        if not find:
            return None
        info_tuple = find[0]
        return {
            'id': int(info_tuple[0]),
            'rarity': int(info_tuple[1]),
            'index': int(info_tuple[2]),
            'kind': 2,
        }
    return None


# 获取本地路径位置
def get_local_path(data_type, lang, filename=None):
    if data_type == '':
        pass
    else:
        if filename is None:
            return os.path.join(DATA_PATH, data_type, lang)
        else:
            return os.path.join(DATA_PATH, data_type, lang, filename)


def get_skip_summon_id_list():
    content, result = read_file(SKIP_SUMMON_ID_LIST_PATH)
    if not result:
        return []
    else:
        raw_list = content.split('\n')
        skip_id_list = []
        for skip_id_text in raw_list:
            skip_id_text = skip_id_text.strip()
            if skip_id_text == '':
                continue
            if skip_id_text[0:1] == '#':
                continue
            try:
                skip_id_list.append(int(skip_id_text))
            except ValueError:
                continue
        return skip_id_list
