import os
from module_huiji.danteng_lib import save_to_csv, load_json


BASE_PATH = r'E:\Temp\job'


# 根据读取到的数据修改
def temp_json_to_excel():

    jp_base_path = os.path.join(BASE_PATH, 'jp')
    en_base_path = os.path.join(BASE_PATH, 'en')
    file_list = os.listdir(jp_base_path)

    job_data = {}

    for filename in file_list:
        jp_job_json = load_json(os.path.join(jp_base_path, filename))
        en_job_json = load_json(os.path.join(en_base_path, filename))

        for job_id in jp_job_json['jobs']:
            jp_job_info = jp_job_json['jobs'][job_id]
            en_job_info = en_job_json['jobs'][job_id]

            job_data[job_id] = {
                'id': job_id,
                'category': filename.replace('.json', ''),
                'images': jp_job_info['images'].replace('_1_01', ''),
                'type': jp_job_info['master']['type'],
                'name_jp': jp_job_info['master']['name'],
                'name_en': en_job_info['master']['name'],
                'weapon1': jp_job_info['master']['weapon1'],
                'weapon2': jp_job_info['master']['weapon2'],
                'comment_jp': jp_job_info['master']['comment'],
                'comment_en': en_job_info['master']['comment'],
            }

    headers = ['id', 'category', 'images', 'type', 'name_jp', 'name_en', 'weapon1', 'weapon2', 'comment_jp', 'comment_en']
    save_to_csv(job_data, headers, r'E:\Temp\job\job.csv')


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
