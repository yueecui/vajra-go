from danteng_lib import read_file


def get_skip_list(skip_list_filename):
    content, result = read_file(skip_list_filename)
    if not result:
        return []
    else:
        return content.split('\n')
