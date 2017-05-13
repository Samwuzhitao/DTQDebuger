pyinstaller -F -w -i ./data./dtq.ico DTQPutty.py
del DTQPutty.spec
del *.pyc
del *.txt
rd /s /q build
copy dist/DTQPutty.exe ./DTQPutty.exe
rd /s /q dist
