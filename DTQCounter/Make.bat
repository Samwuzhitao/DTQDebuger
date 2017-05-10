pyinstaller -F -w -i ./data./dtq.ico DTQDataLost.py
del DTQDataLost.spec
del *.pyc
rd /s /q build
copy dist/DTQDataLost.exe ./DTQDataLost.exe
rd /s /q dist
