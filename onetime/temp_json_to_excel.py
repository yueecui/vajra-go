import mwparserfromhell
import os
from huijiWiki import HuijiWiki
from SaveToExcel import save_to_excel
from danteng_lib import save_to_csv, load_json


JSON_PATH = r'E:\GBF\data\item.json'


# 根据读取到的数据修改
def temp_json_to_excel():
    headers = ['item_id']

    # 获取数据列表
    json_data = load_json(JSON_PATH)

    for one_row in json_data:
        for key in one_row.keys():
            if key not in headers:
                headers.append(key)

    # 生成excel数据
    save_filepath = os.path.join('data', 'Temp_json.csv')
    save_to_csv(json_data, headers, save_filepath)


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
    temp_json_to_excel()
    # try_download_img()
