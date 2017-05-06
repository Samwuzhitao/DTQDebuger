pyinstaller -F -w -i ./data./dtq.ico DTQDebuger.py
del DTQDebuger.spec
del *.pyc
del *.txt
rd /s /q build
copy dist/DTQDebuger.exe ./DTQDebuger.exe
rd /s /q dist
