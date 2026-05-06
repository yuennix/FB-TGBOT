#DECODED BY NETZ
import os
import sys
import re
import random
import string
import time
import platform
import requests
import subprocess
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from faker import Faker
import logging

osxd = os.system
os.system('cls' if platform.system().lower() == 'windows' else 'clear')

print('\033[92;1m>>\033[1;37m Installing missing modules ...')
osxd('pip uninstall requests chardet urllib3 idna certifi -y;pip install chardet urllib3 idna certifi requests bs4')
osxd('pip install faker')

# ANSI color codes
W = '\033[97m'  # White
G = '\033[92m'  # Green
R = '\033[91m'  # Red
V = '\033[1;34m'  # Blue
B = '\033[1;30m'  # Black
RESET = '\033[0m'  # Reset

# Initialize Faker and UserAgent
fake = Faker()
ua = UserAgent()

# ==================== CONFIGURATION (KEPT AS REQUESTED) ====================
CONFIG = {
    "output_dir": os.path.expanduser("~/CYBERX") if platform.system().lower() != 'android' else "/sdcard/CYBERX",
    "auto_create_file": "Auto_Creat.txt",
    "id_auto_create_file": "/sdcard/Id_Auto_Creat.txt",
    "2fa_key_file": "/sdcard/2fa_key.txt",
    "default_password_file": "2FA/default_password.txt",
    "mail_reject_file": "mail_reject.txt",
    "proxy_url": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=100000&country=all&ssl=all&anonymity=all",
    "temp_mail_api": "https://api.internal.temp-mail.io/api/v3/email",
    "facebook_reg_url": "https://x.facebook.com/reg",
    "facebook_submit_url": "https://www.facebook.com/reg/submit/",
    "mail_otp_api": "https://tools.dongvanfb.net/api/get_messages_oauth2",
}

# Ensure output directory exists
os.makedirs(CONFIG["output_dir"], exist_ok=True)

# File storage functions
def save_to_file(data: str, file_path: str):
    """Save data to file in plain text."""
    full_path = os.path.join(CONFIG["output_dir"], file_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "a", encoding="utf-8") as f:
        f.write(data + "\n")

# Device information (for Android-specific properties)
try:
    android_version = subprocess.check_output('getprop ro.build.version.release', shell=True).decode('utf-8').strip()
    model = subprocess.check_output('getprop ro.product.model', shell=True).decode('utf-8').strip()
    build = subprocess.check_output('getprop ro.build.id', shell=True).decode('utf-8').strip()
    fbmf = subprocess.check_output('getprop ro.product.manufacturer', shell=True).decode('utf-8').strip()
    fbbd = subprocess.check_output('getprop ro.product.brand', shell=True).decode('utf-8').strip()
    fbca = subprocess.check_output('getprop ro.product.cpu.abilist', shell=True).decode('utf-8').replace(',', ':').strip()
    fbdm = f"{{density=2.25,height={subprocess.check_output('getprop ro.hwui.text_large_cache_height', shell=True).decode('utf-8').strip()},width={subprocess.check_output('getprop ro.hwui.text_large_cache_width', shell=True).decode('utf-8').strip()}}}"
    try:
        fbcr = subprocess.check_output('getprop gsm.operator.alpha', shell=True).decode('utf-8').split(',')[0].strip()
    except:
        fbcr = 'ZONG'
except:
    android_version, model, build, fbmf, fbbd, fbca, fbdm, fbcr = '10', 'Unknown', 'Unknown', 'Unknown', 'Unknown', 'arm64-v8a', '{density=2.25,height=720,width=1280}', 'ZONG'

device = {
    'android_version': android_version,
    'model': model,
    'build': build,
    'fblc': 'en_US',
    'fbmf': fbmf,
    'fbbd': fbbd,
    'fbdv': model,
    'fbsv': android_version,
    'fbca': fbca,
    'fbdm': fbdm
}

# Proxy handling
def load_proxies():
    proxy_url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=100000&country=all&ssl=all&anonymity=all"
    try:
        response = requests.get(proxy_url)
        if response.status_code == 200:
            return [proxy.strip() for proxy in response.text.splitlines()]
        return []
    except requests.exceptions.RequestException:
        return []

proxies_list = load_proxies()

def get_random_proxy():
    if proxies_list:
        return {"http": f"socks4://{random.choice(proxies_list)}"}
    return None

# User-Agent generation
ua = UserAgent()
def ugenX():
    ualist = [ua.random for _ in range(50)]
    return str(random.choice(ualist))

# ==================== FULL UGEN LIST (Original) ====================
ugen = []
rr = random.randint
for xd in range(10000):
    build_b = random.choice(["001","002","003","011","012","014","015","020","021","022","023","024"])
    bl_typ = random.choice(["TKQ1","SKQ1","TP1A","RKQ1","SP1A","RP1A","PPR1","QP1A"])
    oppo = random.choice(["CPH2461","CPH2451","PCGM00","PBBM00","PFZM10","PGGM10","PECT30","PCHM10","PEAT00","PEYM00","PESM10","PFGM00"])
    infinix = random.choice(["Infinix X669C","Infinix X6823","Infinix X676C","Infinix X683","Infinix X689C","Infinix X6811","Infinix X612B","Infinix X6810","Infinix X665E"])
    redmi = random.choice(["2211133G","M2004J19C","22041219I","22101316UG","2209116AG","M2010J19SY","M2012K11C","Redmi Note 7","Redmi Note 8","Redmi Note 5"])
    um2 = f"Mozilla/5.0 (Linux; Android {str(rr(6,12))}; {oppo} Build/{bl_typ}.{str(rr(120000,220000))}.{build_b}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(rr(80,114))}.0.{str(rr(4200,5400))}.{str(rr(70,150))} Mobile Safari/537.36"
    um1 = f"Mozilla/5.0 (Linux; Android {str(rr(6,12))}; {redmi} Build/{bl_typ}.{str(rr(120000,220000))}.{build_b}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(rr(80,114))}.0.{str(rr(4200,5400))}.{str(rr(70,150))} Mobile Safari/537.36"
    um3 = f"Mozilla/5.0 (Linux; Android {str(rr(6,12))}; {infinix} Build/{bl_typ}.{str(rr(120000,220000))}.{build_b}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{str(rr(80,114))}.0.{str(rr(4200,5400))}.{str(rr(70,150))} Mobile Safari/537.36"
    um4 = f"Mozilla/5.0 (Linux; Android {str(rr(6,12))}; {infinix}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{str(rr(100,114))}.0.{str(rr(4900,5700))}.{str(rr(70,150))} Mobile Safari/537.36"
    ugen.append(um2)
    ugen.append(um3)
    ugen.append(um1)
    ugen.append(um4)

# Name and password generation
first_names = ["Maria", "Ana", "Joy", "Grace", "Angel", "Angela", "Christine", "Kristine", "Michelle", "Shiela", "Jennifer", "Jessica", "Janine", "Paul", "Mark", "John", "Michael", "Daniel", "David", "James"]
surnames = ["Santos", "Reyes", "Cruz", "Bautista", "Garcia", "Mendoza", "Flores", "Gonzales", "Ramos", "Aquino"]

def get_bd_name():
    return random.choice(first_names), random.choice(surnames)

def get_pass():
    name_part = ''.join(random.choices(string.ascii_letters, k=random.randint(5, 7)))
    name_part = name_part.capitalize() if random.choice([True, False]) else name_part.lower()
    symbol_part = ''.join(random.choices('!@#$%^&*()_+=', k=random.randint(2, 3)))
    digit_part = ''.join(random.choices(string.digits, k=random.randint(2, 4)))
    return name_part + symbol_part + digit_part

def khryden_email():
    name = fake.first_name() + fake.last_name()
    username = re.sub(r'[^a-zA-Z]', '', name).lower()
    number = random.randint(1000, 9999)
    return f"{username}{number}@khryden.xyz"

# HTML form extractor
def extractor(data):
    soup = BeautifulSoup(data, "html.parser")
    data = {}
    for inputs in soup.find_all("input"):
        name = inputs.get("name")
        value = inputs.get("value")
        if name:
            data[name] = value
    return data

# Banner
def banner():
    os.system('cls' if platform.system().lower() == 'windows' else 'clear')
    print(f"""{G}
 █████╗ ██╗   ██╗████████╗ ██████╗       {R}███████╗██████╗ 
██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗      {R}██╔════╝██╔══██╗
███████║██║   ██║   ██║   ██║   ██║      {R}█████╗  ██████╔╝
██╔══██║██║   ██║   ██║   ██║   ██║      {R}██╔══╝  ██╔══██╗
██║  ██║╚██████╔╝   ██║   ╚██████╔╝      {R}██║     ██████╔╝
╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝       {R}╚═╝     ╚═════╝
            {W}AUTO FB CREATOR - EMAIL ONLY{W}
{W}─────────────────────────────────────────────{W}""")

def linex():
    print(f"{W}─────────────────────────────────────────────{W}")

oks = []
cps = []

# ==================== MAIN AUTO CREATE (EMAIL ONLY) ====================
def createfb_email_only():
    global oks, cps
    banner()
    
    try:
        num = int(input(f"{W}[{G}•{W}]{G} HOW MANY ACCOUNT {W}:{G} "))
        if num <= 0: raise ValueError
    except:
        print(f"{W}[{R}•{W}]{R} Please enter a valid positive number{W}")
        sys.exit()

    linex()
    print(f"{W}[{G}1{W}]{G} AUTO PASSWORD")
    print(f"{W}[{G}2{W}]{G} CUSTOM PASSWORD")
    linex()
    password_choice = input(f"{W}[{G}•{W}]{G} CHOISE {W}:{G} ")
    pww = get_pass() if password_choice == '1' else input(f"{W}[{G}•{W}]{G} ENTER PASSWORD {W}:{G} ")
    
    linex()
    show_details = input(f"{W}[{G}•{W}]{G} Show All Details y{R}/{G}n {W}:{G} ").lower()
    
    banner()
    print(f"{W}[{G}•{W}]{G} ACCOUNT CREATING STARTED (EMAIL ONLY)")
    print(f'{W}[{G}•{W}]{G} TOTAL ID {W}: {R}{num}{W}')
    linex()

    for _ in range(num):
        try:
            sys.stdout.write(f"\r{W}CYBER-X{G} OK • {len(oks)}   {R}CP • {len(cps)}{W} ")
            sys.stdout.flush()
            
            ses = requests.Session()
            response = ses.get("https://x.facebook.com/reg")
            form = extractor(response.text)
            firstname, lastname = get_bd_name()
            email = khryden_email()

            payload = {
                'ccp': "2",
                'reg_instance': form.get("reg_instance", ""),
                'submission_request': "true",
                'reg_impression_id': form.get("reg_impression_id", ""),
                'ns': "1",
                'logger_id': form.get("logger_id", ""),
                'firstname': firstname,
                'lastname': lastname,
                'birthday_day': str(random.randint(15, 25)),
                'birthday_month': str(random.randint(5, 10)),
                'birthday_year': str(random.randint(1990, 2001)),
                'reg_email__': email,
                'sex': "1",
                'encpass': f'#PWD_BROWSER:0:{int(time.time())}:{pww}',
                'submit': "Sign Up",
                'fb_dtsg': form.get("fb_dtsg", ""),
                'jazoest': form.get("jazoest", ""),
                'lsd': form.get("lsd", "")
            }

            headers = {
                "Host": "m.facebook.com",
                "Connection": "keep-alive",
                "User-Agent": ugenX(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9"
            }

            ses.post("https://www.facebook.com/reg/submit/", data=payload, headers=headers)
            login_coki = ses.cookies.get_dict()

            if "c_user" in login_coki:
                uid = login_coki["c_user"]
                coki = ";".join([f"{key}={value}" for key, value in login_coki.items()])
                
                if show_details == 'y':
                    print(f"\r{W}[{G}•{W}] Name   : {G}{firstname} {lastname}{W}")
                    print(f"\r{W}[{G}•{W}] Email  : {G}{email}{W}")
                    print(f"\r{W}[{G}•{W}] UID    : {G}{uid}{W}")
                    print(f"\r{W}[{G}•{W}] PASS   : {G}{pww}{W}")
                    print(f"\r{G}{uid}|{pww}|{coki}{W}")
                    print(f"{W}─────────────────────────────────────────────{W}")
                else:
                    print(f"\r{G}CYBER-X{W}-{G}[OK] {uid} | {pww}")

                save_to_file(f"{uid}|{pww}|{coki}", CONFIG["auto_create_file"])
                oks.append(uid)

            time.sleep(1.5)
        except:
            time.sleep(8)
            continue

    print(' ')
    linex()
    print(f'{W}[{G}•{W}]{G} The process has completed')
    linex()
    print(f'{W}[{G}•{W}]{G} Total OK {W}: {G}{len(oks)}')
    print(f'{W}[{R}•{W}]{G} Total CP {W}: {R}{len(cps)}')
    linex()
    input(f'{W}[{G}•{W}]{G} Press Enter to Exit... ')
    sys.exit()

# ==================== START ====================
if __name__ == "__main__":
    sys.stdout.write('\x1b]2; CYBER-X EMAIL ONLY\x07')
    while True:
        banner()
        print(f"{W}[{G}1{W}]{G} Start Creating Accounts (Email Only)")
        print(f"{W}[{R}0{W}]{R} Exit")
        linex()
        choice = input(f"{W}[{G}•{W}]{G} CHOISE {W}:{G} ").strip()
        
        if choice == '1':
            createfb_email_only()
        elif choice in ['0', '00']:
            print(f"{G}Thank You For Using CYBER-X Tool!{W}")
            break
        else:
            print(f"{R}Invalid Choice!{W}")
            time.sleep(1)