from danteng_lib import read_file
from config import SKIP_LIST_PATH


# 获取图片跳过的文件地址
def get_skip_list():
    content, result = read_file(SKIP_LIST_PATH)
    if not result:
        return []
    else:
        return content.split('\n')
