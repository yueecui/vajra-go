@venv\Scripts\pyinstaller -c --onefile --version-file "VERSION_INFO" --workpath "build" --distpath "dist" --icon="res\vajra.ico" -y "vajra_go.py"
@pause