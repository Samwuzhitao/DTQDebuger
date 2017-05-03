pyinstaller -F -w -i ./data./dtq.ico DTQDebuger.py
del DTQDebuger.spec
del *.pyc
rd /s /q build
copy dist/DTQDebuger.exe ./DTQDebuger.exe
rd /s /q dist
