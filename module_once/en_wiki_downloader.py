from module_huiji.danteng_lib import load_json, log
from module_huiji.huijiWiki import HuijiWiki
import requests
import json
import os


def download_en_wiki_summon():
    summon_dict = load_json('en_summon_list.json')

    page_ids = []
    for page_info in summon_dict['query']['categorymembers']:
        if page_info['title'].find('Summons List') > -1:
            continue
        page_ids.append(str(page_info['pageid']))

        if len(page_ids) == 25:
            url = f'https://gbf.wiki/api.php?action=query&pageids={"|".join(page_ids)}&prop=revisions&rvprop=content&format=json'
            response = requests.get(url)
            if response.status_code == 200:
                response_data = json.loads(response.text)
                for r_page_id, r_page_detail in response_data['query']['pages'].items():
                    title = HuijiWiki.filename_fix(r_page_detail["title"])
                    save_path = os.path.join('data', 'en_wiki_summon', f'{title}.txt')
                    if not (os.path.exists(save_path) and os.path.getsize(save_path) > 0):
                        with open(save_path, 'w', encoding='UTF-8') as f:
                            f.write(r_page_detail['revisions'][0]['*'])
                        log(f'文件[{title}]保存完成')
            else:
                raise Exception('请求错误')

            page_ids.clear()


def download_en_wiki_weapon():
    weapon_dict = []
    weapon_category_list_url = r'https://gbf.wiki/api.php?action=query&list=categorymembers&cmtitle=Category:Weapons&cmlimit=500&format=json'
    while True:
        response = requests.get(weapon_category_list_url)
        if response.status_code == 200:
            response_data = json.loads(response.text)
            weapon_dict.extend(response_data['query']['categorymembers'])
            if 'continue' not in response_data:
                break
            weapon_category_list_url = f'https://gbf.wiki/api.php?action=query&list=categorymembers&cmtitle=Category:Weapons&cmlimit=500&format=json&cmcontinue={response_data["continue"]["cmcontinue"]}'
        else:
            raise Exception('请求错误')

    page_ids = []
    for page_info in weapon_dict:
        if page_info['title'].find('Summons List') > -1:
            continue
        page_ids.append(str(page_info['pageid']))

        if len(page_ids) == 25:
            url = f'https://gbf.wiki/api.php?action=query&pageids={"|".join(page_ids)}&prop=revisions&rvprop=content&format=json'
            response = requests.get(url)
            if response.status_code == 200:
                response_data = json.loads(response.text)
                for r_page_id, r_page_detail in response_data['query']['pages'].items():
                    title = HuijiWiki.filename_fix(r_page_detail["title"])
                    save_path = os.path.join('data', 'en_wiki_weapon', f'{title}.txt')
                    if not (os.path.exists(save_path) and os.path.getsize(save_path) > 0):
                        with open(save_path, 'w', encoding='UTF-8') as f:
                            f.write(r_page_detail['revisions'][0]['*'])
                        log(f'文件[{title}]保存完成')
            else:
                raise Exception('请求错误')

            page_ids.clear()


def download_en_wiki_char():
    weapon_dict = []
    weapon_category_list_url = r'https://gbf.wiki/api.php?action=query&list=categorymembers&cmtitle=Category:Characters&cmlimit=500&format=json'
    while True:
        response = requests.get(weapon_category_list_url)
        if response.status_code == 200:
            response_data = json.loads(response.text)
            weapon_dict.extend(response_data['query']['categorymembers'])
            if 'continue' not in response_data:
                break
            weapon_category_list_url = f'https://gbf.wiki/api.php?action=query&list=categorymembers&cmtitle=Category:Characters&cmlimit=500&format=json&cmcontinue={response_data["continue"]["cmcontinue"]}'
        else:
            raise Exception('请求错误')

    page_ids = []
    for page_info in weapon_dict:
        if page_info['title'].find('Summons List') > -1:
            continue
        page_ids.append(str(page_info['pageid']))

        if len(page_ids) == 25:
            url = f'https://gbf.wiki/api.php?action=query&pageids={"|".join(page_ids)}&prop=revisions&rvprop=content&format=json'
            response = requests.get(url)
            if response.status_code == 200:
                response_data = json.loads(response.text)
                for r_page_id, r_page_detail in response_data['query']['pages'].items():
                    title = HuijiWiki.filename_fix(r_page_detail["title"])
                    save_path = os.path.join('data', 'en_wiki_char', f'{title}.txt')
                    if not (os.path.exists(save_path) and os.path.getsize(save_path) > 0):
                        with open(save_path, 'w', encoding='UTF-8') as f:
                            f.write(r_page_detail['revisions'][0]['*'])
                        log(f'文件[{title}]保存完成')
            else:
                raise Exception('请求错误')

            page_ids.clear()


if __name__ == '__main__':
    # download_en_wiki_summon()
    # download_en_wiki_weapon()
    download_en_wiki_char()