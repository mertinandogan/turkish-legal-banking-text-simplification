@echo off
setlocal enabledelayedexpansion

REM --- Script Bilgileri ---
echo ===================================================================
echo Yargi MCP Sunucusu - Kolay Kurulum Script'i (Windows BAT)
echo ===================================================================
echo Bu script, Yargi MCP sunucusunun Claude Desktop'a entegrasyonu
echo icin gerekli olan uv ve fastmcp araclarini kuracak ve ardindan
echo sunucuyu dogru bagimliliklarla Claude Desktop'a kuracaktir.
echo.
echo Devam etmek istiyor musunuz? (E/H):
set /p "continue_script="
if /i not "%continue_script%"=="E" (
    echo Kurulum iptal edildi.
    goto :eof
)
echo.

REM --- Proje ve Claude Araci Bilgileri ---
set MCP_SERVER_SCRIPT_NAME=mcp_server_main.py
set CLAUDE_TOOL_NAME="Yargı MCP"
set DEPENDENCIES_FOR_FASTMCP_INSTALL=--with httpx --with beautifulsoup4 --with markitdown --with pydantic --with aiohttp

REM --- Adim 1: uv Kurulumu ---
echo [ADIM 1/3] uv kontrol ediliyor ve gerekiyorsa kuruluyor...
uv --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   uv zaten kurulu. Versiyon:
    uv --version
) else (
    echo   uv kurulu degil. Kurulum denenecek...
    echo   PowerShell ile uv indirme ve kurma script'i calistirilacak.
    echo   Bu islem icin internet baglantisi gereklidir.
    powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo   HATA: uv PowerShell ile kurulamadi. Alternatif olarak pip/pip3 ile deneniyor...
        pip install uv
        if %errorlevel% neq 0 (
            echo     UYARI: 'pip install uv' basarisiz oldu. 'pip3 install uv' deneniyor...
            pip3 install uv
            if %errorlevel% neq 0 (
                 echo       HATA: uv 'pip3 install uv' ile de kurulamadi. Lutfen https://astral.sh/uv adresinden manuel kurulum yapin.
                 goto :error_exit
            )
        )
    )
    echo   uv basariyla kuruldu (veya kuruluma calisildi). PATH'in guncellenmesi icin terminali yeniden baslatmaniz gerekebilir.
    echo   uv versiyonu kontrol ediliyor:
    set "UV_PATH_CARGO=%USERPROFILE%\.cargo\bin\uv.exe"
    set "UV_PATH_LOCALAPP=%LOCALAPPDATA%\uv\uv.exe"
    
    if exist "%UV_PATH_CARGO%" (
        "%UV_PATH_CARGO%" --version
    ) else if exist "%UV_PATH_LOCALAPP%" (
        "%UV_PATH_LOCALAPP%" --version
    ) else (
        uv --version || (echo HATA: uv kuruldu ancak PATH'de bulunamadi. Lutfen terminali yeniden baslatin veya PATH'i manuel guncelleyin. && goto :error_exit)
    )
)
echo.

REM --- Adim 2: fastmcp CLI Kurulumu ---
echo [ADIM 2/3] fastmcp CLI kontrol ediliyor ve gerekiyorsa kuruluyor...
fastmcp --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   fastmcp CLI zaten kurulu. Versiyon:
    fastmcp --version
) else (
    echo   fastmcp CLI kurulu degil. Kurulum denenecek (uv kullanarak)...
    if exist "%UV_PATH_CARGO%" (
        "%UV_PATH_CARGO%" pip install fastmcp
    ) else if exist "%UV_PATH_LOCALAPP%" (
        "%UV_PATH_LOCALAPP%" pip install fastmcp
    ) else (
        uv pip install fastmcp
    )

    if %errorlevel% neq 0 (
        echo     UYARI: fastmcp CLI 'uv pip install fastmcp' ile kurulamadi. Alternatif olarak pip/pip3 ile deneniyor...
        pip install fastmcp
        if %errorlevel% neq 0 (
            echo       UYARI: fastmcp CLI 'pip install fastmcp' ile de kurulamadi. 'pip3 install fastmcp' deneniyor...
            pip3 install fastmcp
            if %errorlevel% neq 0 (
                 echo         HATA: fastmcp CLI 'pip3 install fastmcp' ile de kurulamadi. Lutfen manuel kurulum yapin.
                 goto :error_exit
            )
        )
    )
    echo   fastmcp CLI basariyla kuruldu (veya kuruluma calisildi).
    echo   fastmcp versiyonu kontrol ediliyor:
    fastmcp --version || (echo HATA: fastmcp kuruldu ancak PATH'de bulunamadi. Lutfen terminali yeniden baslatin veya PATH'i manuel guncelleyin. && goto :error_exit)
)
echo.

REM --- Adim 3: Sunucuyu Claude Desktop'a Kurma ---
echo [ADIM 3/3] %CLAUDE_TOOL_NAME% sunucusu Claude Desktop'a kuruluyor...
if not exist "%MCP_SERVER_SCRIPT_NAME%" (
    echo HATA: Ana sunucu script'i '%MCP_SERVER_SCRIPT_NAME%' bulunamadi.
    echo Lutfen bu script'i '%MCP_SERVER_SCRIPT_NAME%' dosyasinin bulundugu dizinde calistirin.
    goto :error_exit
)

echo   Kullanilacak komut:
echo   fastmcp install %MCP_SERVER_SCRIPT_NAME% --name %CLAUDE_TOOL_NAME% %DEPENDENCIES_FOR_FASTMCP_INSTALL%
echo.

REM fastmcp CLI'nin PATH'de oldugunu varsayiyoruz (bir önceki adimda kontrol edildi)
fastmcp install %MCP_SERVER_SCRIPT_NAME% --name %CLAUDE_TOOL_NAME% %DEPENDENCIES_FOR_FASTMCP_INSTALL%

if %errorlevel% neq 0 (
    echo   HATA: Sunucu Claude Desktop'a 'fastmcp install' komutu ile kurulamadi.
    echo   Lutfen fastmcp CLI'nin duzgun kuruldugundan ve PATH'de oldugundan emin olun.
    echo   Ayrica, Claude Desktop uygulamasinin calisir durumda oldugunu kontrol edin.
    goto :error_exit
)

echo.
echo ===================================================================
echo KURULUM TAMAMLANDI!
echo ===================================================================
echo - %CLAUDE_TOOL_NAME% araci Claude Desktop'a eklenmis olmalidir.
echo - Degisikliklerin etkili olmasi icin Claude Desktop'i yeniden baslatmaniz gerekebilir.
echo - Eger 'uv' veya 'fastmcp' PATH'e yeni eklendiyse, bu script'i calistirdiginiz terminali de
echo   yeniden baslatmaniz gerekebilir.
echo.
goto :eof

:error_exit
echo.
echo !!! KURULUM BASARISIZ OLDU !!!
echo Lutfen yukaridaki hata mesajlarini kontrol edin.
echo.
pause
exit /b 1

:eof
endlocal