@echo off
echo Yargi MCP Kurulum Script'i (install.py) baslatiliyor...

REM Python'in PATH'de oldugunu varsayiyoruz.
REM Kullanici sistemine gore "python" veya "py -3" veya "python3" olabilir.
REM Oncelikle "python" deneyelim.
python install.py
if errorlevel 1 (
    echo "python install.py" komutu basarisiz oldu. "py -3 install.py" deneniyor...
    py -3 install.py
    if errorlevel 1 (
        echo "py -3 install.py" komutu da basarisiz oldu.
        echo Lutfen Python 3'un sisteminizde kurulu ve PATH'de oldugundan emin olun.
    )
)

echo.
pause