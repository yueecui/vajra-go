import mwparserfromhell
import os
import json
from huijiWiki import HuijiWiki
from SaveToExcel import save_to_excel
from danteng_lib import save_to_csv

JSON_PATH = r'E:\GBF\IMAGE\data'


# 根据读取到的数据修改
def weapon_data_to_excel():
    headers = ['id', 'name', 'name_en']
    contents = {}

    # 获取数据列表
    base_path = os.path.join(JSON_PATH, 'weapon')
    page_list = os.listdir(os.path.join(base_path, 'jp'))

    for filename in page_list:
        with open(os.path.join(base_path, 'jp', filename), 'r', encoding='UTF-8') as f:
            item_json = json.loads(f.read())

        with open(os.path.join(base_path, 'en', filename), 'r', encoding='UTF-8') as f:
            item_json_en = json.loads(f.read())

        save_row(headers, contents, item_json, item_json_en)

    # 生成excel数据
    save_filepath = os.path.join('data', 'Weapon_game.csv')
    save_to_csv(contents, headers, save_filepath)

    # sheet_name = 'Weapon'
    # headers = {
    #     sheet_name: headers
    # }
    # contents = {
    #     sheet_name: contents
    # }
    # save_filepath = os.path.join('data', 'Weapon_game.xlsx')
    # save_to_excel(headers, contents, save_filepath)


# 根据读取到的数据修改
def summon_data_to_excel():
    headers = ['id', 'name', 'name_en']
    contents = {}

    # 获取数据列表
    base_path = os.path.join(JSON_PATH, 'summon')
    page_list = os.listdir(os.path.join(base_path, 'jp'))

    for filename in page_list:
        with open(os.path.join(base_path, 'jp', filename), 'r', encoding='UTF-8') as f:
            item_json = json.loads(f.read())

        with open(os.path.join(base_path, 'en', filename), 'r', encoding='UTF-8') as f:
            item_json_en = json.loads(f.read())

        final_uncap_file_path = os.path.join(base_path, 'final_uncap', filename)
        if os.path.exists(final_uncap_file_path):
            with open(final_uncap_file_path, 'r', encoding='UTF-8') as f:
                item_json_fu = json.loads(f.read())
                item_json['final_attack'] = item_json_fu['param']['attack']
                item_json['final_hp'] = item_json_fu['param']['hp']

        save_row(headers, contents, item_json, item_json_en)

    # 生成excel数据
    save_filepath = os.path.join('data', 'Summon_game.csv')
    save_to_csv(contents, headers, save_filepath)


# 保存到excel
def save_row(headers, contents, item_json, item_json_en):
    one_data = {}
    for key, value in item_json.items():
        if type(value) == dict:
            for sub_key, sub_value in value.items():
                name_sub_key = f'{key}.{sub_key}'
                if name_sub_key not in headers:
                    headers.append(name_sub_key)
                one_data[name_sub_key] = sub_value
        else:
            if key not in headers:
                headers.append(key)
            one_data[key] = value
    one_data['name_en'] = item_json_en['name']
    contents[one_data['id']] = one_data


if __name__ == '__main__':
    # weapon_data_to_excel()
    summon_data_to_excel()
