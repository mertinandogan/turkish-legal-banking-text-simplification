@echo off
setlocal enabledelayedexpansion

REM --- Script Bilgileri ---
echo ===================================================================
echo Yargi MCP Sunucusu - Kolay Kurulum Script'i (Windows BAT)
echo ===================================================================
echo Bu script, Yargi MCP sunucusunun Claude Desktop'a entegrasyonu
echo icin gerekli olan uv (fastmcp install komutu icin onerilir) 
echo ve fastmcp araclarini kuracak ve ardindan sunucuyu 
echo dogru bagimliliklarla Claude Desktop'a kuracaktir.
echo.
echo Devam etmek istiyor musunuz? (E/H):
set /p "continue_script="
if /i not "%continue_script%"=="E" (
    echo Kurulum iptal edildi.
    pause
    goto :eof
)
echo.

REM --- Proje ve Claude Araci Bilgileri ---
set MCP_SERVER_SCRIPT_NAME=mcp_server_main.py
set CLAUDE_TOOL_NAME="Yargı MCP"
set DEPENDENCIES_FOR_FASTMCP_INSTALL=--with httpx --with beautifulsoup4 --with markitdown --with pydantic --with aiohttp

REM --- Adim 1: uv Kurulumu 
echo [ADIM 1/3] uv kontrol ediliyor ve gerekiyorsa kuruluyor...
uv --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   uv zaten kurulu. Versiyon:
    uv --version
    set "UV_EXECUTABLE=uv"
) else (
    echo   uv kurulu degil veya PATH'de degil. Kurulum denenecek...
    echo   PowerShell ile uv indirme ve kurma script'i calistirilacak.
    powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if !errorlevel! neq 0 (
        echo   HATA: uv PowerShell ile kurulamadi. Alternatif olarak pip/pip3 ile deneniyor...
        pip install uv
        if !errorlevel! neq 0 (
            echo     UYARI: 'pip install uv' basarisiz oldu. 'pip3 install uv' deneniyor...
            pip3 install uv
            if !errorlevel! neq 0 (
                 echo       HATA: uv 'pip3 install uv' ile de kurulamadi. Lutfen https://astral.sh/uv adresinden manuel kurulum yapin.
                 goto :error_exit
            )
        )
    )
    echo   uv kurulum denemesi tamamlandi.
    set "UV_EXECUTABLE="
    if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
        set "UV_EXECUTABLE=%USERPROFILE%\.cargo\bin\uv.exe"
        echo   uv "%USERPROFILE%\.cargo\bin\" adresinde bulundu.
    ) else if exist "%LOCALAPPDATA%\uv\uv.exe" (
        set "UV_EXECUTABLE=%LOCALAPPDATA%\uv\uv.exe"
        echo   uv "%LOCALAPPDATA%\uv\" adresinde bulundu.
    )
    
    if defined UV_EXECUTABLE (
        "%UV_EXECUTABLE%" --version
        if !errorlevel! neq 0 (
            echo UYARI: uv kuruldu ancak calistirilamiyor. PATH sorunu olabilir. Terminali yeniden baslatin.
            set "UV_EXECUTABLE=uv" 
        )
    ) else (
        uv --version >nul 2>&1
        if !errorlevel! equ 0 (
            echo   uv PATH'de bulundu.
            set "UV_EXECUTABLE=uv"
        ) else (
            echo HATA: uv kuruldu ancak PATH'de bulunamadi veya calistirilamadi.
            echo Lutfen terminali yeniden baslatin veya PATH'i manuel guncelleyin ve uv'nin calistigini dogrulayin.
            goto :error_exit
        )
    )
)
echo.

REM --- Adim 2: fastmcp CLI Kurulumu 
echo [ADIM 2/3] fastmcp CLI kontrol ediliyor ve gerekiyorsa kuruluyor (pip/pip3 kullanarak)...
fastmcp --version >nul 2>&1
if %errorlevel% equ 0 (
    echo   fastmcp CLI zaten kurulu.
    fastmcp --version
    set "FASTMCP_EXECUTABLE=fastmcp"
) else (
    echo   fastmcp CLI kurulu degil veya PATH'de degil. Kurulum denenecek (pip/pip3 ile)...
    pip install fastmcp
    if !errorlevel! neq 0 (
        echo     UYARI: 'pip install fastmcp' basarisiz oldu. 'pip3 install fastmcp' deneniyor...
        pip3 install fastmcp
        if !errorlevel! neq 0 (
            echo       HATA: fastmcp CLI 'pip3 install fastmcp' ile de kurulamadi. Lutfen manuel kurulum yapin.
            goto :error_exit
        )
    )

    fastmcp --version >nul 2>&1
    if !errorlevel! equ 0 (
        echo   fastmcp CLI basariyla kuruldu/bulundu.
        fastmcp --version
        set "FASTMCP_EXECUTABLE=fastmcp"
    ) else (
        echo HATA: fastmcp CLI kurulamadi veya PATH'de bulunamadi.
        echo Lutfen terminali yeniden baslatin veya PATH'i manuel guncelleyin.
        goto :error_exit
    )
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
echo   %FASTMCP_EXECUTABLE% install %MCP_SERVER_SCRIPT_NAME% --name %CLAUDE_TOOL_NAME% %DEPENDENCIES_FOR_FASTMCP_INSTALL%
echo.

"%FASTMCP_EXECUTABLE%" install "%MCP_SERVER_SCRIPT_NAME%" --name %CLAUDE_TOOL_NAME% %DEPENDENCIES_FOR_FASTMCP_INSTALL%

if !errorlevel! neq 0 (
    echo   HATA: Sunucu Claude Desktop'a 'fastmcp install' komutu ile kurulamadi.
    echo   Lutfen '%FASTMCP_EXECUTABLE%' komutunun duzgun calistigindan emin olun.
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
pause
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