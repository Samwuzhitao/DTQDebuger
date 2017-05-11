pyinstaller -F -w -i ./data./dtq.ico DTQCounter.py
del DTQCounter.spec
del *.pyc
rd /s /q build
copy dist/DTQCounter.exe ./DTQCounter.exe
rd /s /q dist
