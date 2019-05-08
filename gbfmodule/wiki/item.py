import os
from huijiWikiTabx import HuijiWikiTabx
from danteng_lib import log, read_file, load_json
from config import IMAGE_PATH, WIKITEXT_PATH
from pyvar_to_lua import pyvar_to_lua


item_jp_json_path = r'data\item_jp.json'
item_en_json_path = r'data\item_en.json'


def update_item_tabx(cfg, args):
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["item"]}.tabx'

    item_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    # 从本地json添加新数据
    item_jp_json = load_json(item_jp_json_path)

    for item_info in item_jp_json:
        item_id = int(item_info['item_id'])
        row_info = item_tabx.get_row(item_id)
        item_tabx.mod_row(item_id, generate_item_row(item_info, row_info))

    # 从本地json添加新数据
    item_en_json = load_json(item_en_json_path)

    for item_info in item_en_json:
        item_id = int(item_info['item_id'])
        row_info = item_tabx.get_row(item_id)
        if row_info:
            row_info['name_en'] = item_info['name']
            row_info['comment_en'] = item_info['comment'].replace('\n', '<br>').strip()
        item_tabx.mod_row(item_id, row_info)

    # 从本地图标文件添加空的数据
    # 先检查本地
    item_icon_path = os.path.join(IMAGE_PATH, 'item', 'article_s')
    all_item_icon_list = os.listdir(item_icon_path)
    for sub_path_name in all_item_icon_list:
        name_split = os.path.splitext(sub_path_name)

        if len(name_split) != 2 or name_split[1] != '.jpg':
            continue

        item_id = int(name_split[0])

        if not item_tabx.has_row(item_id):
            item_tabx.mod_row(item_id, generate_item_row(blank_item_row()))

    # 保存
    item_tabx.save()


def generate_item_row(item_info, row_info=None):
    if row_info is None:
        row_info = {}

    # 召唤石图鉴数据
    temp_row = {
        'name_jp': item_info['name'],
        'name_en': row_info['name_en'] if 'name_en' in row_info else '',
        'name_chs': row_info['name_chs'] if 'name_chs' in row_info else '',
        'search_nickname': row_info['search_nickname'] if 'search_nickname' in row_info else [],
        'seq_id': int(item_info['seq_id']),
        'category_type': item_info['category_type'],
        'comment_jp': item_info['comment'].replace('\n', '<br>').strip(),
        'comment_en': row_info['comment_en'] if 'comment_en' in row_info else '',
        'comment_chs': row_info['comment_chs'] if 'comment_chs' in row_info else '',
    }
    return temp_row


def blank_item_row():
    return {
        'name': '',
        'comment': '',
        'seq_id': 999999,
        'category_type': []
    }


def update_item_auto_db(cfg, args):
    gbf_wiki = cfg['wiki']
    tabx_page_title = f'Data:{cfg["TABX"]["item"]}.tabx'

    item_tabx = HuijiWikiTabx(gbf_wiki, tabx_page_title, 'ID')

    item_db_auto = {}
    item_replace_map = {}

    for item_id, item_info in item_tabx.get_all_data().items():
        item_name = item_info['name_chs'] if item_info['name_chs'] else item_info['name_jp']
        if not item_name:
            continue

        item_db_auto[item_id] = {
            'id': item_id,
            'name': item_name
        }

        if not item_info['name_chs']:
            continue

        item_replace_map[item_info['name_chs']] = item_id
        for nickname in item_info['nickname']:
            item_replace_map[nickname] = item_id
        for nickname in item_info['search_nickname']:
            item_replace_map[nickname] = item_id

    output = []

    output.append('----------------------------------------------')
    output.append('-- 本文件由机器人自动维护，请勿手工修改')
    output.append('-- 内容来源：[[Data:物品列表.tabx]]')
    output.append('-- 手工添加请访问：[[Module:Util/LinkNickname]]')
    output.append('----------------------------------------------')
    output.append('')
    output.append('local p = {}')
    output.append('')
    output.append('p.replace = ' + pyvar_to_lua(item_replace_map).dump_to_luatable())
    output.append('')
    output.append('p.db = ' + pyvar_to_lua(item_db_auto).dump_to_luatable())
    output.append('')
    output.append('return p')

    page_title = 'Module:Item/AutoDB'
    page_content = '\n'.join(output)

    wikitext_file_path = os.path.join(WIKITEXT_PATH, gbf_wiki.filename_fix(f'{page_title}.txt'))

    gbf_wiki.edit(page_title, page_content, filepath=wikitext_file_path, compare_flag=True)
    gbf_wiki.wait_threads()
