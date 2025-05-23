@echo off
setlocal enabledelayedexpansion

REM --- Script Bilgileri ---
echo ===================================================================
echo Yargi MCP Sunucusu - Kolay Kurulum Script'i (Windows BAT) - DEBUG v3
echo ===================================================================
echo Bu script, Yargi MCP sunucusunun Claude Desktop'a entegrasyonu
echo icin gerekli olan uv ve fastmcp araclarini kuracak ve ardindan
echo sunucuyu dogru bagimliliklarla Claude Desktop'a kuracaktir.
echo.
echo Devam etmek istiyor musunuz? (E/H):
set /p "continue_script="
if /i not "%continue_script%"=="E" (
    echo Kurulum iptal edildi.
    pause
    goto :eof
)
echo.
echo DEBUG: Kullanici onayi alindi.

REM --- Proje ve Claude Araci Bilgileri ---
set MCP_SERVER_SCRIPT_NAME=mcp_server_main.py
set CLAUDE_TOOL_NAME="Yargı MCP"
set DEPENDENCIES_FOR_FASTMCP_INSTALL=--with httpx --with beautifulsoup4 --with markitdown --with pydantic --with aiohttp
echo DEBUG: Temel degiskenler ayarlandi:
echo DEBUG:   MCP_SERVER_SCRIPT_NAME=%MCP_SERVER_SCRIPT_NAME%
echo DEBUG:   CLAUDE_TOOL_NAME=%CLAUDE_TOOL_NAME%
echo DEBUG:   DEPENDENCIES_FOR_FASTMCP_INSTALL=%DEPENDENCIES_FOR_FASTMCP_INSTALL%

REM --- Adim 1: uv Kurulumu (fastmcp install komutunun daha iyi calismasi icin onerilir) ---
echo.
echo [ADIM 1/3] uv kontrol ediliyor ve gerekiyorsa kuruluyor...
set "UV_EXECUTABLE=uv" REM Varsayilan olarak PATH'den denenecek

echo DEBUG: Adim 1.1 - Ilk 'uv --version' denemesi (hatalar gizlendi)...
uv --version >nul 2>&1
echo DEBUG: Adim 1.1 - Hata Seviyesi: !errorlevel!
if !errorlevel! equ 0 (
    echo   uv zaten kurulu (PATH'de bulundu). Versiyon:
    uv --version
    echo DEBUG: Adim 1.1.1 - Basarili. UV_EXECUTABLE 'uv' olarak ayarlandi.
) else (
    echo DEBUG: Adim 1.2 - 'uv --version' basarisiz. Kurulum adimlari basliyor.
    echo   uv kurulu degil veya PATH'de degil. Kurulum denenecek...
    
    echo DEBUG: Adim 1.3 - PowerShell ile uv kurulumu deneniyor...
    powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
    echo DEBUG: Adim 1.4 - PowerShell denemesi tamamladi, errorlevel: !errorlevel!
    
    if !errorlevel! neq 0 (
        echo   HATA: uv PowerShell ile kurulamadi. Alternatif olarak pip/pip3 ile deneniyor...
        echo DEBUG: Adim 1.5 - 'pip install uv' deneniyor...
        pip install uv
        echo DEBUG: Adim 1.6 - 'pip install uv' tamamladi, errorlevel: !errorlevel!
        if !errorlevel! neq 0 (
            echo     UYARI: 'pip install uv' basarisiz oldu. 'pip3 install uv' deneniyor...
            echo DEBUG: Adim 1.7 - 'pip3 install uv' deneniyor...
            pip3 install uv
            echo DEBUG: Adim 1.8 - 'pip3 install uv' tamamladi, errorlevel: !errorlevel!
            if !errorlevel! neq 0 (
                 echo       HATA: uv 'pip3 install uv' ile de kurulamadi. Lutfen https://astral.sh/uv adresinden manuel kurulum yapin.
                 echo DEBUG: Adim 1.9 - Tum uv kurulum denemeleri basarisiz.
                 goto :error_exit
            )
        )
    )
    echo DEBUG: Adim 1.10 - Kurulum denemelerinden sonra uv versiyonu kontrol ediliyor...
    set "UV_EXECUTABLE_TEMP="
    if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
        set "UV_EXECUTABLE_TEMP=%USERPROFILE%\.cargo\bin\uv.exe"
        echo DEBUG: Adim 1.11a - uv "%UV_EXECUTABLE_TEMP%" adresinde bulundu.
    ) else if exist "%LOCALAPPDATA%\uv\uv.exe" (
        set "UV_EXECUTABLE_TEMP=%LOCALAPPDATA%\uv\uv.exe"
        echo DEBUG: Adim 1.11b - uv "%UV_EXECUTABLE_TEMP%" adresinde bulundu.
    )

    if defined UV_EXECUTABLE_TEMP (
        echo DEBUG: Adim 1.12 - Belirli yoldan uv calistiriliyor: "%UV_EXECUTABLE_TEMP%" --version
        "%UV_EXECUTABLE_TEMP%" --version >nul 2>&1
        echo DEBUG: Adim 1.12 - Hata Seviyesi: !errorlevel!
        if !errorlevel! equ 0 (
            set "UV_EXECUTABLE=%UV_EXECUTABLE_TEMP%"
            echo   uv basariyla bulundu/kuruldu: "%UV_EXECUTABLE%"
            "%UV_EXECUTABLE%" --version
        ) else (
            echo   UYARI: uv özel yolda bulundu ("%UV_EXECUTABLE_TEMP%") ama calistirilamadi. PATH'den 'uv' deneniyor.
            set "UV_EXECUTABLE=uv" 
        )
    ) else (
        echo DEBUG: Adim 1.13 - uv özel yollarda bulunamadi. PATH'den 'uv' deneniyor.
        set "UV_EXECUTABLE=uv"
    )
    
    echo DEBUG: Adim 1.14 - Son uv kontrolu: "%UV_EXECUTABLE%" --version (hatalar gizlendi)
    "%UV_EXECUTABLE%" --version >nul 2>&1
    echo DEBUG: Adim 1.14 - Hata Seviyesi: !errorlevel!
    if !errorlevel! neq 0 (
        echo HATA: uv kuruldu/bulundu olarak isaretlendi ancak '%UV_EXECUTABLE% --version' komutu basarisiz oldu.
        echo Lutfen terminalinizi yeniden baslatin ve PATH'i kontrol edin.
        echo DEBUG: Adim 1.15 - Son uv kontrolu basarisiz.
        goto :error_exit
    )
    echo   uv versiyonu:
    "%UV_EXECUTABLE%" --version
)
echo DEBUG: Adim 1 - uv bolumu tamamlandi. Kullanilacak UV_EXECUTABLE: "%UV_EXECUTABLE%"
echo.

REM --- Adim 2: fastmcp CLI Kurulumu (uv KULLANILMADAN, pip/pip3 ile) ---
echo [ADIM 2/3] fastmcp CLI kontrol ediliyor ve gerekiyorsa kuruluyor (pip/pip3 kullanarak)...
set "FASTMCP_EXECUTABLE=fastmcp" REM Varsayilan

echo DEBUG: Adim 2.1 - Ilk 'fastmcp --version' denemesi (hatalar gizlendi)...
fastmcp --version >nul 2>&1
echo DEBUG: Adim 2.1 - Hata Seviyesi: !errorlevel!
if !errorlevel! equ 0 (
    echo   fastmcp CLI zaten kurulu (PATH'de bulundu). Versiyon:
    fastmcp --version
    echo DEBUG: Adim 2.1.1 - Basarili. FASTMCP_EXECUTABLE 'fastmcp' olarak ayarlandi.
) else (
    echo DEBUG: Adim 2.2 - 'fastmcp --version' basarisiz. Kurulum adimlari basliyor.
    echo   fastmcp CLI kurulu degil veya PATH'de degil. Kurulum denenecek (pip/pip3 ile)...
    
    echo DEBUG: Adim 2.3 - 'pip install fastmcp' deneniyor...
    pip install fastmcp
    echo DEBUG: Adim 2.4 - 'pip install fastmcp' tamamladi, errorlevel: !errorlevel!
    
    if !errorlevel! neq 0 (
        echo     UYARI: 'pip install fastmcp' basarisiz oldu. 'pip3 install fastmcp' deneniyor...
        echo DEBUG: Adim 2.5 - 'pip3 install fastmcp' deneniyor...
        pip3 install fastmcp
        echo DEBUG: Adim 2.6 - 'pip3 install fastmcp' tamamladi, errorlevel: !errorlevel!
        if !errorlevel! neq 0 (
            echo       HATA: fastmcp CLI 'pip3 install fastmcp' ile de kurulamadi. Lutfen manuel kurulum yapin.
            echo DEBUG: Adim 2.7 - Tum fastmcp pip/pip3 kurulum denemeleri basarisiz.
            goto :error_exit
        )
    )
    echo DEBUG: Adim 2.8 - fastmcp kurulum denemesi tamamlandi. PATH'den tekrar kontrol ediliyor...
    fastmcp --version >nul 2>&1
    echo DEBUG: Adim 2.8 - Hata Seviyesi: !errorlevel!
    if !errorlevel! equ 0 (
        echo   fastmcp CLI basariyla kuruldu. Versiyon:
        fastmcp --version
        set "FASTMCP_EXECUTABLE=fastmcp"
    ) else (
        echo HATA: fastmcp CLI kuruldu ancak PATH'de bulunamadi veya calistirilamadi.
        echo Lutfen terminali yeniden baslatin veya PATH'i manuel guncelleyin.
        echo DEBUG: Adim 2.9 - Son fastmcp kontrolu basarisiz.
        goto :error_exit
    )
)
echo DEBUG: Adim 2 - fastmcp CLI bolumu tamamlandi. Kullanilacak FASTMCP_EXECUTABLE: "%FASTMCP_EXECUTABLE%"
echo.

REM --- Adim 3: Sunucuyu Claude Desktop'a Kurma ---
echo [ADIM 3/3] %CLAUDE_TOOL_NAME% sunucusu Claude Desktop'a kuruluyor...
if not exist "%MCP_SERVER_SCRIPT_NAME%" (
    echo HATA: Ana sunucu script'i '%MCP_SERVER_SCRIPT_NAME%' bulunamadi.
    echo Lutfen bu script'i '%MCP_SERVER_SCRIPT_NAME%' dosyasinin bulundugu dizinde calistirin.
    echo DEBUG: Adim 3.1 - Sunucu script dosyasi bulunamadi.
    goto :error_exit
)
echo DEBUG: Adim 3.2 - Sunucu script dosyasi bulundu.

echo   Kullanilacak komut:
echo   "%FASTMCP_EXECUTABLE%" install "%MCP_SERVER_SCRIPT_NAME%" --name %CLAUDE_TOOL_NAME% %DEPENDENCIES_FOR_FASTMCP_INSTALL%
echo.
echo DEBUG: Adim 3.3 - 'fastmcp install' komutu calistiriliyor...
"%FASTMCP_EXECUTABLE%" install "%MCP_SERVER_SCRIPT_NAME%" --name %CLAUDE_TOOL_NAME% %DEPENDENCIES_FOR_FASTMCP_INSTALL%
echo DEBUG: Adim 3.4 - 'fastmcp install' komutu tamamladi, errorlevel: !errorlevel!

if !errorlevel! neq 0 (
    echo   HATA: Sunucu Claude Desktop'a 'fastmcp install' komutu ile kurulamadi.
    echo   Lutfen '%FASTMCP_EXECUTABLE%' komutunun duzgun calistigindan emin olun.
    echo   Ayrica, Claude Desktop uygulamasinin calisir durumda oldugunu kontrol edin.
    echo DEBUG: Adim 3.5 - 'fastmcp install' basarisiz.
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
echo Lutfen yukaridaki hata mesajlarini ve DEBUG adimlarini kontrol edin.
echo Hatanin olustugu son DEBUG adimi sorunu bulmaniza yardimci olabilir.
echo.
pause
exit /b 1

:eof
endlocal