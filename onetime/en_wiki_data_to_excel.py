import mwparserfromhell
import os
from huijiWiki import HuijiWiki
from SaveToExcel import save_to_excel
from danteng_lib import save_to_csv

WEAPON_PATH = r'E:\GBF\data\en_wiki_weapon'
SUMMON_PATH = r'E:\GBF\data\en_wiki_summon'
CHAR_PATH = r'E:\GBF\data\en_wiki_char'


# 根据读取到的数据修改
def en_wiki_weapon_to_excel():
    headers = ['page_title']
    contents = {}

    # 获取数据列表
    page_list = os.listdir(WEAPON_PATH)
    temp_list = []

    for filename in page_list:
        page_title = os.path.splitext(filename)[0]
        with open(os.path.join(WEAPON_PATH, filename), 'r', encoding='UTF-8') as f:
            wikitext = f.read()
        mwparser = mwparserfromhell.parse(wikitext)
        page_template_lists = mwparser.filter_templates(recursive=False)

        has_info_count = 0
        for page_template in page_template_lists:
            template_name = page_template.name.strip().lower()
            if template_name == 'weapon':
                save_row(headers, contents, page_title, page_template)
                has_info_count += 1
                break
            for param_info in page_template.params:
                param_name = param_info.name
                if param_name == 'id':
                    save_row(headers, contents, page_title, page_template)
                    has_info_count += 1
                    break
        if has_info_count == 0:
            temp_list.append(page_title)

    print('\n'.join(temp_list))

    # 生成excel数据
    sheet_name = 'Weapon'
    headers = {
        sheet_name: headers
    }
    contents = {
        sheet_name: contents
    }
    save_filepath = os.path.join('data', sheet_name + '.xlsx')
    save_to_excel(headers, contents, save_filepath)


# 根据读取到的数据修改
def en_wiki_summon_to_excel():
    headers = ['page_title']
    contents = {}

    # 获取数据列表
    page_list = os.listdir(SUMMON_PATH)
    temp_list = []

    for filename in page_list:
        page_title = os.path.splitext(filename)[0]
        with open(os.path.join(SUMMON_PATH, filename), 'r', encoding='UTF-8') as f:
            wikitext = f.read()
        mwparser = mwparserfromhell.parse(wikitext)
        page_template_lists = mwparser.filter_templates(recursive=False)

        has_info_count = 0
        for page_template in page_template_lists:
            template_name = page_template.name.strip().lower()
            if template_name == 'summon':
                save_row(headers, contents, page_title, page_template)
                has_info_count += 1
                break
            for param_info in page_template.params:
                param_name = param_info.name
                if param_name == 'id':
                    save_row(headers, contents, page_title, page_template)
                    has_info_count += 1
                    break
        if has_info_count == 0:
            temp_list.append(page_title)

    print('\n'.join(temp_list))

    # 生成excel数据
    save_filepath = os.path.join('data', 'Summon_en_wiki.csv')
    save_to_csv(contents, headers, save_filepath)

    # sheet_name = 'Summon'
    # headers = {
    #     sheet_name: headers
    # }
    # contents = {
    #     sheet_name: contents
    # }
    # save_filepath = os.path.join('data', sheet_name + '.xlsx')
    # save_to_excel(headers, contents, save_filepath)


# 根据读取到的数据修改
def en_wiki_char_to_excel():
    headers = ['page_title']
    contents = {}

    # 获取数据列表
    page_list = os.listdir(CHAR_PATH)
    temp_list = []

    for filename in page_list:
        page_title = os.path.splitext(filename)[0]
        with open(os.path.join(CHAR_PATH, filename), 'r', encoding='UTF-8') as f:
            wikitext = f.read()
        mwparser = mwparserfromhell.parse(wikitext)
        page_template_lists = mwparser.filter_templates(recursive=False)

        has_info_count = 0
        for page_template in page_template_lists:
            template_name = page_template.name.strip().lower()
            if template_name == 'character':
                save_row(headers, contents, page_title, page_template)
                has_info_count += 1
                break
            for param_info in page_template.params:
                param_name = param_info.name
                if param_name == 'id':
                    save_row(headers, contents, page_title, page_template)
                    has_info_count += 1
                    break
        if has_info_count == 0:
            temp_list.append(page_title)

    print('\n'.join(temp_list))

    # 生成excel数据
    save_filepath = os.path.join('data', 'Character_en_wiki.csv')
    save_to_csv(contents, headers, save_filepath)

    # sheet_name = 'Summon'
    # headers = {
    #     sheet_name: headers
    # }
    # contents = {
    #     sheet_name: contents
    # }
    # save_filepath = os.path.join('data', sheet_name + '.xlsx')
    # save_to_excel(headers, contents, save_filepath)


# 保存到excel
def save_row(headers, contents, page_title, template):
    one_data = {
        'page_title': page_title
    }
    for param_info in template.params:
        param_name = param_info.name.strip()
        if param_name not in headers:
            headers.append(param_name)
        one_data[param_name] = param_info.value.strip()
    contents[page_title] = one_data


if __name__ == '__main__':
    # en_wiki_weapon_to_excel()
    # en_wiki_summon_to_excel()
    en_wiki_char_to_excel()
