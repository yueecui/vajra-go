# 说明

VajraGo是用于爬取是[碧蓝幻想中文维基](https://gbf.huijiwiki.com)所需的数据、图片资源，以及协助进行Wiki更新的小工具

# 安装
最高测试过的环境版本为[Python 3.9.10(64-bit)](https://www.python.org/downloads/release/python-3910/)

```bash
pip install -r requirements.txt
```

# 配置文件
请参考[config.ini.example](config.ini.example)文件，去掉example后缀后放到脚本运行目录下

具体请参考范例运行目录的内容

# 功能使用

请参考范例运行目录的说明和bat指令

# 打包
脚本使用pyinstaller打包，打包指令附于pack.bat中

```bash
venv\Scripts\pyinstaller -c --onefile --version-file "VERSION_INFO" --workpath "build" --distpath "dist" --icon="res\vajra.ico" -y "vajra_go.py"
```
