#!/bin/bash

# --- Script Bilgileri ---
echo "==================================================================="
echo " Yargi MCP Sunucusu - Kurulum Başlatıcı (macOS/Linux)"
echo "==================================================================="
echo " Bu script, Yargi MCP sunucusunun kurulumu için gerekli olan"
echo " Python script'ini (install.py) çalıştıracaktır."
echo ""
read -p "Devam etmek istiyor musunuz? (E/H): " continue_script
if [[ ! "$continue_script" =~ ^[Ee]$ ]]; then
    echo "Kurulum iptal edildi."
    exit 0
fi
echo ""

# --- Python Yorumlayıcısını Bul ve install.py'yi Çalıştır ---
PYTHON_EXECUTABLE=""

# Öncelikle python3'ü dene
if command -v python3 &>/dev/null; then
    PYTHON_EXECUTABLE="python3"
# Sonra python'u dene (Python 3 olduğundan emin olmak için install.py içinde kontrol var)
elif command -v python &>/dev/null; then
    PYTHON_EXECUTABLE="python"
fi

if [ -z "$PYTHON_EXECUTABLE" ]; then
    echo "[HATA] Sisteminizde Python 3 bulunamadı veya PATH'e eklenmemiş."
    echo "Lütfen Python 3'ü (https://www.python.org/downloads/) kurun."
    exit 1
fi

echo "[INFO] '$PYTHON_EXECUTABLE install.py' komutu çalıştırılıyor..."
echo "-------------------------------------------------------------------"

"$PYTHON_EXECUTABLE" install.py

# install.py script'inin çıkış kodunu kontrol et
INSTALL_EXIT_CODE=$?

echo "-------------------------------------------------------------------"
if [ $INSTALL_EXIT_CODE -eq 0 ]; then
    echo "[INFO] install.py script'i başarıyla tamamlandı."
else
    echo "[HATA] install.py script'i bir hatayla sonlandı (Çıkış Kodu: $INSTALL_EXIT_CODE)."
    echo "[HATA] Lütfen yukarıdaki hata mesajlarını kontrol edin."
fi

echo ""
# Pencerenin hemen kapanmaması için (özellikle çift tıklanarak çalıştırılırsa)
read -p "Kurulum script'i tamamlandı. Çıkmak için Enter tuşuna basın..."

exit $INSTALL_EXIT_CODE