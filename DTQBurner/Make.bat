pyinstaller -F -w -i ./image/dtq.ico DTQBurner.py
del DTQBurner.spec
del *.pyc
rd /s /q build
copy dist/DTQBurner.exe ./DTQBurner.exe
rd /s /q dist
