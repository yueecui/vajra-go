# -*- coding:utf-8 -*-

"""

local tbl = {
  aa = 1,
  bb = {2 , 3 , {aa = 1, bb = 1}},
  [1] = 1,
  4,
  cc = 1+2,
  dd = 3 == 3
}

{1, 2, 3} ->
- evaled as dict
- evaled as array

python dict is unhashable
"""

import re


def read_as_int(s):
    int(s)


def read_as_str(s):
    return s


def read(s):
    if s.startswith("{"):
        return s, type("table")
    else:
        try:
            value = eval(s)
            return value, type(value)
        except NameError:
            return s, type("")


class LuaTable(object):
    def __init__(self):
        self.m_Dict = {}
        self.m_List = []

    def index(self, key):
        if isinstance(key, int):
            if key < len(self.m_List):
                return self.m_List[key]
        assert (isinstance(key, str))
        return self.m_Dict[key]

    def len(self):
        return len(self.m_List)

    def insert(self, v):
        self.m_List.append(v)

    def set(self, k, v):
        self.m_Dict[k] = v

    def ipairs(self):
        for i, v in enumerate(self.m_List):
            yield (i + 1, v)

    def pairs(self):
        for i, v in enumerate(self.m_List):
            yield (i + 1, v)
        for k, v in self.m_Dict.iteritems():
            yield (k, v)

    def dump_to_luatable(self):

        def _luatable_open(luatbl):
            luatbl += "{"
            return luatbl

        def _luatable_close(luatbl):
            luatbl += "}"
            return luatbl

        def _luatable_readvalue(value):
            if isinstance(value, int) or isinstance(value, float):
                return "%s" % str(value).lower()
            elif isinstance(value, str):
                return "\"%s\"" % value
            else:
                return _luatable_packup(value)

        def _luatable_insert(luatbl, value):
            luatbl += "%s, " % _luatable_readvalue(value)
            return luatbl

        def _luatable_setkv(luatbl, key, value):
            luatbl += "[%s] = %s, " % (
                _luatable_readvalue(key),
                _luatable_readvalue(value)
            )
            return luatbl

        def _luatable_packup(luatbl_obj):
            luatbl = ""
            luatbl = _luatable_open(luatbl)
            for k, v in luatbl_obj.m_Dict.items():
                luatbl = _luatable_setkv(luatbl, k, v)
            for v in luatbl_obj.m_List:
                luatbl = _luatable_insert(luatbl, v)
            luatbl = _luatable_close(luatbl)
            return luatbl

        return _luatable_packup(self)


find_pair = {
    "table_str": ("{", "}"),
    "key_str": ("[", "]")
}


def generate_pair_finder(pair):
    def pair_finder(s):
        block_cnt = 0
        for i, c in enumerate(s):
            if c == pair[0]: block_cnt += 1
            if c == pair[1]: block_cnt -= 1
            if block_cnt == 0:
                assert (s[i] == pair[1])
                return s[0:i + 1], 0, i + 1
        return "", 0, 0

    return pair_finder


find_table_str = generate_pair_finder(find_pair["table_str"])
find_key_str = generate_pair_finder(find_pair["key_str"])


def find_all_atoms(s):
    s += ","
    block_cnt = 0
    var_left = 0
    lst = []
    i = 0
    while (i < len(s)):
        c = s[i]
        if c == "{":
            block_cnt += 1
        elif c == "}":
            block_cnt -= 1
        elif block_cnt == 0 and c == ",":
            lst.append(s[var_left:i].strip())
            var_left = i + 1
        i += 1
    return lst


match_key_value = "^\[?(?P<value>\w+)\]? *= *(?P<key>.+)"


def split_atoms(atom):
    match_obj = re.match(match_key_value, atom)
    if match_obj:
        key = match_obj.group("value")
        value = match_obj.group("key")
        return True, key, value
    return False, atom, None


def luatbl_to_pydict(table):
    luatbl = LuaTable()
    lst = find_all_atoms(table[1:-1])
    for atom in lst:
        if atom.startswith("{"):
            luatbl.insert(luatbl_to_pydict(atom))
        else:
            valid_kv, key, value = split_atoms(atom)
            if valid_kv:
                if value.startswith("{"):
                    luatbl.set(key, luatbl_to_pydict(value))
                else:
                    value, t = read(value)
                    luatbl.set(key, value)
            else:
                luatbl.insert(key)
    return luatbl


# 将python基础变量类型转成lua
def pyvar_to_lua(input_value):
    if type(input_value) == list:
        luatbl = LuaTable()
        for value in input_value:
            luatbl.insert(pyvar_to_lua(value))
        return luatbl
    elif type(input_value) == dict:
        luatbl = LuaTable()
        for key, value in input_value.items():
            luatbl.set(key, pyvar_to_lua(value))
        return luatbl
    elif type(input_value) == str or type(input_value) == int or type(input_value) == float or type(input_value) == bool:
        return input_value
    else:
        try:
            return str(input_value)
        except:
            return None


if __name__ == "__main__":
    test = {
        'a': 'bgfsb',
        'b': 2,
        '4asd': 5,
        3: 1,
        'test': [1,{'x':'你好'},[44,55,66],7],
        'cacfs': {
            'bh': 'dada',
            1: '4'
        }
    }
    tesvfvfs = pyvar_to_lua(test)
    luatbl11 = luatbl_to_pydict("{a = 1, b = 2, {a = 1 , b = 2, 3, 4, 5}, c, d, 1 , 2, [c] = 1}")
    print(luatbl11.dump_to_luatable())



