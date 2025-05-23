# install.py

import subprocess
import sys
import os
import shutil
import platform
from urllib.parse import urlencode, urljoin, quote 

# --- Yapılandırma ---
MCP_SERVER_SCRIPT_NAME = "mcp_server_main.py"
CLAUDE_TOOL_NAME = "Yargı MCP" 
DEPENDENCIES_FOR_FASTMCP = [
    "httpx", "beautifulsoup4", "markitdown", "pydantic", "aiohttp"
]

# --- Yardımcı Fonksiyonlar ---
def print_info(message):
    print(f"[INFO] {message}")

def print_warning(message):
    print(f"[UYARI] {message}")

def print_error(message):
    print(f"[HATA] {message}")

def command_exists(command_parts):
    """Bir komutun sistemde var olup olmadığını kontrol eder ve yolunu döndürür."""
    try:
        command_to_check = command_parts[0] if isinstance(command_parts, list) else command_parts
        found_path = shutil.which(command_to_check)
        if found_path:
            return found_path
        if platform.system() == "Windows" and not command_to_check.endswith(".exe"):
            # .exe olmadan da PATH'de bulunabilir (örn: pyenv shims)
            # ama yine de .exe ile de kontrol edelim
            path_with_exe = shutil.which(command_to_check + ".exe")
            if path_with_exe:
                return path_with_exe
        return None
    except Exception:
        return None

def run_command(command_parts, capture_output_flag=False, check_return_code=True, shell=False, cwd=None, log_output_on_success=False):
    """Verilen komutu çalıştırır."""
    cmd_str_for_log = ' '.join(command_parts) if isinstance(command_parts, list) else command_parts
    print_info(f"Komut çalıştırılıyor: {cmd_str_for_log}")
    
    kwargs = {
        "text": True,
        "shell": shell,
        "cwd": cwd,
        "encoding": 'utf-8',
        "errors": 'replace' # Handles potential decoding errors in output
    }

    if capture_output_flag:
        kwargs["capture_output"] = True
    # Else, stdout/stderr go to console by default (unless shell redirects them)

    try:
        process = subprocess.run(command_parts, **kwargs)
        
        if capture_output_flag:
            if log_output_on_success and process.returncode == 0:
                if process.stdout: print_info(f"Stdout:\n{process.stdout.strip()}")
                if process.stderr: print_warning(f"Stderr:\n{process.stderr.strip()}")
            elif process.returncode != 0: # Always log output on error if captured
                if process.stdout: print_error(f"Hata Stdout:\n{process.stdout.strip()}")
                if process.stderr: print_error(f"Hata Stderr:\n{process.stderr.strip()}")

        if check_return_code and process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd_str_for_log, output=process.stdout, stderr=process.stderr)
            
        return process
    except subprocess.CalledProcessError as e:
        # run_command already printed details if capture_output_flag was true
        if not capture_output_flag: # If output went to console, just print a simpler error
             print_error(f"Komut hatası (return code {e.returncode}): {cmd_str_for_log}")
        raise 
    except FileNotFoundError:
        print_error(f"Komut bulunamadı: {command_parts[0] if isinstance(command_parts, list) else command_parts.split()[0]}")
        raise
    except Exception as e:
        print_error(f"Komut çalıştırılırken beklenmedik hata ({cmd_str_for_log}): {type(e).__name__} - {e}")
        raise

def get_python_executable():
    """Kullanılabilir Python 3 çalıştırılabilir dosyasını bulur."""
    print_info("Python 3 yorumlayıcısı aranıyor...")
    # Önce mevcut çalışan Python'u dene
    current_python = sys.executable
    if current_python:
        try:
            print_info(f"Mevcut Python deneniyor: {current_python}")
            result = run_command([current_python, "-c", "import sys; assert sys.version_info.major == 3, 'Not Python 3'"], capture_output_flag=True, log_output_on_success=False)
            if result.returncode == 0:
                print_info(f"Kullanılacak Python: {current_python}")
                return current_python
        except Exception as e:
            print_warning(f"Mevcut Python ({current_python}) kontrol edilirken sorun: {e}")

    # PATH'deki python3 ve python komutlarını dene
    for cmd_name in ["python3", "python"]:
        found_cmd_path = command_exists(cmd_name)
        if found_cmd_path:
            try:
                print_info(f"PATH'de bulunan '{cmd_name}' deneniyor: {found_cmd_path}")
                result = run_command([found_cmd_path, "-c", "import sys; assert sys.version_info.major == 3, 'Not Python 3'; print(sys.executable)"], capture_output_flag=True, log_output_on_success=False)
                if result.returncode == 0 and result.stdout:
                    resolved_path = result.stdout.strip()
                    print_info(f"Kullanılacak Python: {resolved_path} ('{cmd_name}' komutu ile bulundu)")
                    return resolved_path
            except Exception as e:
                print_warning(f"'{cmd_name}' ({found_cmd_path}) kontrol edilirken sorun: {e}")
                
    print_error("Python 3 sisteminizde bulunamadı veya PATH'e doğru şekilde eklenmemiş.")
    print_error("Lütfen Python 3'ü (https://www.python.org/downloads/) kurun.")
    sys.exit(1)


# --- Kurulum Fonksiyonları ---
def install_uv(python_exe_path):
    print_info("Adım 1/3: uv kontrol ediliyor/kuruluyor...")
    uv_executable = command_exists("uv")
    if uv_executable:
        print_info(f"uv zaten kurulu: {uv_executable}")
        run_command([uv_executable, "--version"], capture_output_flag=True, log_output_on_success=True)
        return uv_executable

    print_info("uv kurulu değil. Kurulum denenecek...")
    try:
        if platform.system() == "Windows":
            print_info("PowerShell ile uv indirme ve kurma script'i çalıştırılacak.")
            run_command([
                "powershell", "-ExecutionPolicy", "Bypass", "-NoProfile", "-NonInteractive",
                "-Command", "try { irm https://astral.sh/uv/install.ps1 | iex } catch { Write-Error $_; exit 1 }"
            ], shell=False)
        else: 
            print_info("curl ile uv kurulum script'i çalıştırılacak.")
            process = subprocess.run("curl -LsSf https://astral.sh/uv/install.sh | sh", shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if process.stdout: print_info(f"uv install script stdout:\n{process.stdout}")
            if process.stderr: print_warning(f"uv install script stderr:\n{process.stderr}")
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, "curl ... | sh")
        
        uv_executable = command_exists("uv") 
        if not uv_executable: # PATH'e hemen yansımamış olabilir, bilinen yerleri kontrol et
            common_paths_uv = []
            if platform.system() == "Windows":
                cargo_uv_path = os.path.join(os.environ.get("USERPROFILE", ""), ".cargo", "bin", "uv.exe")
                localapp_uv_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "uv", "uv.exe")
                if os.path.exists(cargo_uv_path): common_paths_uv.append(cargo_uv_path)
                if os.path.exists(localapp_uv_path): common_paths_uv.append(localapp_uv_path)
            else: # macOS / Linux
                common_paths_uv.extend([
                    os.path.join(os.environ.get("HOME", ""), ".cargo", "bin", "uv"),
                    os.path.join(os.environ.get("HOME", ""), ".local", "bin", "uv")
                ])
            for p_uv in common_paths_uv:
                if command_exists(p_uv): uv_executable = p_uv; break
        
        if uv_executable and command_exists(uv_executable):
            print_info(f"uv başarıyla kuruldu/bulundu: {uv_executable}")
            run_command([uv_executable, "--version"], capture_output_flag=True, log_output_on_success=True)
            return uv_executable
        else: # Son çare pip
            print_warning("uv resmi script ile kuruldu/bulundu ancak PATH'de doğrulanamadı. pip ile deneniyor...")
            run_command([python_exe_path, "-m", "pip", "install", "uv"])
            uv_executable = command_exists("uv")
            if uv_executable:
                print_info(f"uv pip ile başarıyla kuruldu: {uv_executable}")
                run_command([uv_executable, "--version"], capture_output_flag=True, log_output_on_success=True)
                return uv_executable
            print_error("uv pip ile de kurulamadı. Lütfen manuel kurulum yapın: https://astral.sh/uv")
            return None
    except Exception as e:
        print_error(f"uv kurulumu sırasında genel bir hata oluştu: {e}")
        print_warning("Lütfen uv'yi manuel olarak kurmayı deneyin: https://astral.sh/uv")
        return None

def install_fastmcp_cli(python_exe_path, uv_exe_path): # uv_exe_path artık kullanılmıyor
    """fastmcp CLI'yi kontrol eder ve gerekirse pip/pip3 ile kurar."""
    print_info("Adım 2/3: fastmcp CLI kontrol ediliyor/kuruluyor...")
    fastmcp_executable = command_exists("fastmcp")
    if fastmcp_executable:
        print_info(f"fastmcp CLI zaten kurulu: {fastmcp_executable}")
        run_command([fastmcp_executable, "version"], capture_output_flag=True, log_output_on_success=True)
        return fastmcp_executable

    print_info("fastmcp CLI kurulu değil. pip/pip3 ile kurulum denenecek...")
    try:
        pip_cmd_to_try = [python_exe_path, "-m", "pip", "install", "fastmcp"]
        print_info(f"{' '.join(pip_cmd_to_try)} komutu deneniyor...")
        run_command(pip_cmd_to_try)
        
        fastmcp_executable = command_exists("fastmcp")
        if fastmcp_executable:
            print_info(f"fastmcp CLI başarıyla kuruldu: {fastmcp_executable}")
            run_command([fastmcp_executable, "version"], capture_output_flag=True, log_output_on_success=True)
            return fastmcp_executable
        else: 
            scripts_dir = os.path.dirname(python_exe_path)
            if platform.system() == "Windows" and not scripts_dir.lower().endswith("scripts"):
                 scripts_dir = os.path.join(scripts_dir, "Scripts")
            potential_fastmcp_path = os.path.join(scripts_dir, "fastmcp.exe" if platform.system() == "Windows" else "fastmcp")
            if command_exists(potential_fastmcp_path):
                print_info(f"fastmcp CLI şu yolda bulundu: {potential_fastmcp_path}")
                run_command([potential_fastmcp_path, "version"], capture_output_flag=True, log_output_on_success=True)
                return potential_fastmcp_path
            else:
                print_error("fastmcp CLI kuruldu ancak PATH'de veya bilinen Python script yollarında bulunamadı.")
                print_error("Lütfen terminalinizi yeniden başlatın veya PATH'i manuel güncelleyin.")
                return None
    except Exception as e:
        print_error(f"fastmcp CLI kurulumu sırasında hata oluştu: {e}")
        return None

def install_tool_to_claude_desktop(fastmcp_exe_path):
    """Yargı MCP sunucusunu Claude Desktop'a kurar."""
    print_info(f"Adım 3/3: \"{CLAUDE_TOOL_NAME}\" Claude Desktop'a kuruluyor...")
    if not os.path.exists(MCP_SERVER_SCRIPT_NAME):
        print_error(f"Ana sunucu script'i '{MCP_SERVER_SCRIPT_NAME}' bulunamadı.")
        print_error("Lütfen bu script'i ana sunucu script'inin bulunduğu dizinde çalıştırın.")
        return False

    dependencies_cmd_part = []
    for dep in DEPENDENCIES_FOR_FASTMCP:
        dependencies_cmd_part.extend(["--with", dep])
    
    install_command = [
        fastmcp_exe_path, "install", MCP_SERVER_SCRIPT_NAME,
        "--name", CLAUDE_TOOL_NAME
    ] + dependencies_cmd_part
    
    try:
        process = run_command(install_command, capture_output_flag=True, check_return_code=False, log_output_on_success=False)
        if process.returncode == 0:
            print_info(f"\"{CLAUDE_TOOL_NAME}\" başarıyla Claude Desktop'a kuruldu/güncellendi.")
            if process.stdout: print_info(f"fastmcp install stdout:\n{process.stdout.strip()}")
            if process.stderr: print_warning(f"fastmcp install stderr:\n{process.stderr.strip()}")
            return True
        else:
            error_output = (process.stdout or "") + (process.stderr or "")
            if "claude app not found" in error_output.lower():
                print_error("Claude Desktop uygulaması sisteminizde bulunamadı veya algılanamadı.")
                print_error("Lütfen Claude Desktop'ın kurulu ve çalışır durumda olduğundan emin olun.")
                print_error("Claude Desktop'ı https://claude.ai/download adresinden indirebilirsiniz.")
            else:
                print_error(f"Sunucu Claude Desktop'a kurulurken hata oluştu (return code {process.returncode}).")
                print_error("Lütfen fastmcp CLI'nin düzgün çalıştığından emin olun.")
                if process.stderr: print_error(f"fastmcp install stderr:\n{process.stderr.strip()}")
                if process.stdout: print_info(f"fastmcp install stdout (hata durumunda):\n{process.stdout.strip()}")
            return False
    except Exception as e:
        print_error(f"Sunucu Claude Desktop'a kurulurken genel bir hata oluştu: {e}")
        return False

# --- Ana Kurulum Mantığı ---
def main():
    print("===================================================================")
    print(" Yargi MCP Sunucusu - Python Kurulum Script'i")
    print("===================================================================")
    
    if platform.system() == "Windows":
        confirm = input("Bu script, uv ve fastmcp araclarini kuracak ve Yargi MCP sunucusunu Claude Desktop'a entegre edecektir. Devam etmek istiyor musunuz? (E/H): ")
        if confirm.lower() != 'e':
            print_info("Kurulum kullanıcı tarafından iptal edildi.")
            sys.exit(0)
    
    python_executable = get_python_executable()
    uv_executable_path = install_uv(python_executable) # uv hala öneriliyor fastmcp install için
    
    fastmcp_executable_path = install_fastmcp_cli(python_executable, uv_executable_path) # uv_exe_path burada kullanılmıyor
    if not fastmcp_executable_path:
        print_error("fastmcp CLI kurulumu başarısız oldu. Kurulum sonlandırılıyor.")
        sys.exit(1)

    if not install_tool_to_claude_desktop(fastmcp_executable_path):
        print_error("Claude Desktop'a kurulum başarısız oldu.")
        sys.exit(1)

    print_info("===================================================================")
    print_info(" KURULUM BAŞARIYLA TAMAMLANDI!")
    print_info("===================================================================")
    print_info(f"- \"{CLAUDE_TOOL_NAME}\" aracı Claude Desktop'a eklenmiş olmalıdır.")
    print_info("- Değişikliklerin etkili olması için Claude Desktop'ı yeniden başlatmanız gerekebilir.")
    print_info("- Eğer uv veya fastmcp PATH'e yeni eklendiyse, terminalinizi de yeniden başlatmanız gerekebilir.")

if __name__ == "__main__":
    try:
        main()
    except SystemExit: 
        pass # sys.exit() çağrıldığında script sonlansın
    except Exception as e:
        print_error(f"Beklenmedik bir genel hata oluştu: {e}")
        sys.exit(1)
    finally:
        if platform.system() == "Windows":
            input("Çıkmak için Enter tuşuna basın...")
        else:
            print("Kurulum script'i tamamlandı.")