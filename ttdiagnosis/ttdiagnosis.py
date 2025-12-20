import os
import re
import json
import struct
import socket
import asyncio
import fnmatch
from datetime import datetime
import requests

from ttdiagnosis.ttapi import TTApi


class TTDiagnosis:
    """TycheTools diagnosis class"""

    CMD_APP_LIST   = 0x0401
    CMD_GW_STATUS  = 0x0004
    CMD_NODE_LIST  = 0x0101
    GW_SOCKET_FILE = "/tmp/ttgw.socket"
    PING_URL       = "ecoaas.tychetools.com"

    def __init__(self, client, user, password):
        self.client = client
        self.user = user
        self.password = password
        self.ttapi = TTApi(self.client)
        self.diagnosis = {
            "general": {
                "hostname": "",
                "localtime": "",
                "uptime_s": 0,
                "board": "",
                "gitrev": "",
                "machine": "",
                "bt_mac": "",
                "public_ip": ""
            },
            "hardware": {
                "hw_version": "",
                "enclosure": "",
                "shield_present": False,
                "leds": ""
            },
            "proccesses": {
                "gateway": {
                    "status": "",
                    "init": False,
                    "gw_addr": 0,
                    "netkey": "",
                    "nodes": 0,
                    "coverage": {},
                    "listener": False,
                    "scanning": False,
                    "provisioning": False,
                    "firmware": {
                        "version": ""
                    },
                    "library": {
                        "version": ""
                    },
                    "app": {
                        "version": ""
                    },
                    "apps": {
                        "backend": "",
                        "snmp": "",
                        "mqtt": "",
                        "influx": "",
                        "csv": "",
                        "net_eng": "",
                        "air_quality": ""
                    }
                },
                "ble_config": {
                    "status": "",
                    "version": ""
                },
                "ssh_tunnel": {
                    "status": "",
                    "ip": "",
                    "port": 0
                }
            },
            "interfaces": [],
            "connection": {
                "connected": "",
                "interface": "",
                "tx_bytes": 0,
                "rx_bytes": 0,
                "ping": {
                    "response": True,
                    "rtt_ms": 0
                },
                "wifi": {
                    "status": "",
                    "ssid": "",
                    "passwd": "",
                    "signal": 0
                },
                "gsm": {
                    "status": "",
                    "man": "",
                    "apn": "",
                    "operator": "",
                    "tech": "",
                    "signal": 0
                }
            },
            "system": {
                "cpu_num": 0,
                "cpu_perc": 0,
                "cpu_temp": 0,
                "filesys": "",
                "disk_size_mb": 0,
                "disk_available_mb": 0,
                "ram_size_kb": 0,
                "ram_available_kb": 0,
                "usb_devices": []
            }
        }

    async def shell(self, cmd: str):
        """Run shell commands"""
        process = await asyncio.create_subprocess_shell(cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT)
        stdout, _ = await process.communicate()
        retval = await process.wait()
        output = stdout.decode()
        return retval, output

    def cat(self, fpath):
        """Reads files using Python"""
        try:
            with open(os.path.expanduser(fpath), "r", encoding="UTF-8") as file:
                return file.readlines()
        except FileNotFoundError:
            return []

    def request(self, method, url, body, timeout):
        """API request funcion"""
        try:
            response = requests.request(method, url, json=body, timeout=timeout)
        except requests.exceptions.ConnectionError:
            print("HTTP connection error")
            return None
        except requests.exceptions.ReadTimeout:
            print("HTTP connection timeout")
            return None
        return response

    def gw_send_command(self, cmd, params=None):
        """Send a command to gateway with sockets"""
        gw_socket = socket.socket(socket.AF_UNIX)
        if not os.path.exists(self.GW_SOCKET_FILE):
            return None
        if params is None:
            params = {}
        gw_socket.connect(self.GW_SOCKET_FILE)
        json_cmd = {"command_id": cmd, "params": params}
        json_bytes = json.dumps(json_cmd).encode()
        data_cmd = bytearray()
        data_cmd += struct.pack("<I", len(json_bytes))
        data_cmd += json_bytes
        try:
            gw_socket.sendall(data_cmd)
        except BrokenPipeError:
            print("Broken pipe")
            return None
        raw_data = gw_socket.recv(1024)
        if not raw_data:
            print("Server ended connection")
            return None
        data_len = int.from_bytes(raw_data[0:4], "little")
        data = bytearray()
        data += raw_data[4:]
        while len(data) < data_len:
            raw_data = gw_socket.recv(1024)
            if not raw_data:
                print("Server ended connection")
                return None
            data += raw_data
        gw_socket.close()
        return json.loads(data.decode())

    async def get_hostname(self):
        """Returns hostname"""
        _, output = await self.shell("hostname")
        return output.strip()

    async def get_date(self):
        """Returns date in ISO8601 format"""
        return datetime.now().astimezone().isoformat(timespec="seconds")

    async def get_uptime(self):
        """Returns uptime"""
        line = self.cat("/proc/uptime")[0]
        return int(float(line.split()[0].strip()))

    async def get_ttversion(self):
        """Returns board, gitrev and machine"""
        board = gitrev = machine = None
        lines = self.cat("/etc/ttversion")
        for line in lines:
            param = line.split("=", 1)
            if param[0] == "BOARD":
                board = param[1].strip()
            if param[0] == "GITREV":
                gitrev = param[1].strip()
            if param[0] == "MACHINE":
                machine = param[1].strip()
        return {
            "board": board,
            "gitrev": gitrev,
            "machine": machine
        }

    async def get_bt_mac(self):
        """Returns Bluetooth MAC"""
        mac = None
        retval, output = await self.shell("hciconfig")
        if retval == 0 and output is not None:
            lines = output.splitlines()
            if len(lines) > 2:
                mac = lines[1].split()[2]
        return mac

    async def get_public_ip(self):
        """Returns public IP"""
        _, output = await self.shell("curl -s ifconfig.me")
        return output

    async def get_ifaces(self):
        """Returns devices"""
        ifaces, iface_en, iface_type = [], None, None
        retval, output = await self.shell("nmcli -t d")
        ex_ifaces = ("lo", "p2p-dev-*", "sit*")
        if retval == 0 and output is not None:
            for line in output.splitlines():
                device = line.split(":", 4)[0].strip()
                match = [fnmatch.fnmatch(device, ex_if) for ex_if in ex_ifaces]
                if any(match):
                    continue
                ifaces.append(device)
                status = line.split(":", 4)[2].strip()
                if status == "connected":
                    iface_en = line.split(":", 4)[0].strip()
                    iface_type = line.split(":", 4)[1].strip()
        return ifaces, iface_en, iface_type

    async def get_iface_info(self, iface: str):
        """Returns iface properties"""
        conntype = mac = state = ip = None
        retval, output = await self.shell(f"nmcli -t d show {iface}")
        if retval == 0 and output is not None:
            for line in output.splitlines():
                param = line.split(":", 1)
                if param[0] == "GENERAL.TYPE":
                    conntype = param[1]
                if param[0] == "GENERAL.HWADDR":
                    mac = param[1]
                if param[0] == "GENERAL.STATE":
                    if "(connected)" in param[1]:
                        state = "Connected"
                    else:
                        state = "Disconnected"
                if param[0] == "IP4.ADDRESS[1]":
                    ip = param[1]
        return {
            "conntype": conntype,
            "mac": mac,
            "state": state,
            "ip": ip
        }

    async def get_iface_txrx(self, iface: str):
        """Returns iface TX and RX bytes"""
        iface_tx = iface_rx = None
        retval, output = await self.shell(f"ip -s link show {iface}")
        if retval == 0 and output is not None:
            lines = output.splitlines()
            for i, line in enumerate(lines):
                if "TX" in line:
                    iface_tx = int(lines[i+1].split()[0])
                if "RX" in line:
                    iface_rx = int(lines[i+1].split()[0])
        return {
            "tx": iface_tx,
            "rx": iface_rx
        }

    async def get_wifi_info(self):
        """Returns WiFi info"""
        conn = ssid = passwd = signal = None
        retval, output = await self.shell("nmcli -t d")
        if retval == 0 and output is not None:
            for line in output.splitlines():
                line = line.split(":")
                if line[1] == "wifi" and line[2] == "connected":
                    conn = line[3]
        if conn is not None:
            retval, output = await self.shell(f"nmcli -s -t c show {conn}")
            if retval == 0 and output is not None:
                for line in output.splitlines():
                    param = line.split(":", 1)
                    if param[0] == "802-11-wireless.ssid":
                        ssid = param[1].strip()
                    if param[0] == "802-11-wireless-security.psk":
                        passwd = param[1].strip()
                    if param[0] == "802-11-wireless.ssid":
                        signal = param[1].strip()
            retval, output = await self.shell(
                "nmcli -t -f IN-USE,SIGNAL device wifi")
            if retval == 0 and output is not None:
                for line in output.splitlines():
                    param = line.split(":", 1)
                    if param[0] == "*":
                        signal = param[1].strip()
        return {
            "ssid": ssid,
            "passwd": passwd,
            "signal": signal
        }

    async def get_gsm_info(self):
        """Returns GSM info"""
        status = man = apn = tech = operator = signal = None
        retval, output = await self.shell("mmcli -K d --modem 0")
        if retval == 0 and output is not None:
            for line in output.splitlines():
                param = line.split(":", 1)
                if param[0] == "modem.generic.state":
                    status = param[1].strip()
                if param[0] == "modem.generic.manufacturer":
                    man = param[1].strip()
                if param[0] == "apn": #Not working
                    apn = param[1].strip()
                if param[0] == "odem.generic.access-technologies.value[1]":
                    tech = param[1].strip()
                if param[0] == "modem.3gpp.operator-name":
                    operator = param[1].strip()
                if param[0] == "modem.generic.signal-quality.value":
                    signal = param[1].strip()
        return {
            "status": status,
            "man": man,
            "apn": apn,
            "operator": operator,
            "tech": tech,
            "signal": signal
        }

    async def get_ping(self):
        """Returns ping to TycheTools ECOaaS info"""
        response = rtt = None
        retval, output = await self.shell(f"ping -q -c3 -W5 {self.PING_URL}")
        if retval != 0 or output is None:
            response = False
        else:
            response = True
            match = re.search(".*=\s[\d\.]+\/([\d\.]+)", output)
            if match:
                rtt = float(match.groups()[0])
        return {
            "response": response,
            "rtt": rtt
        }

    async def get_gw_info(self):
        """Returns gateway info"""
        status = "Disabled"
        init = lib_ver = fw_ver = app_ver = gw_addr = netkey = nodes = \
            listener = scanning = provisioning = None
        resp = self.gw_send_command(self.CMD_GW_STATUS)
        if resp is not None:
            status = "Enabled"
            init = resp["success"]
            if init:
                data = resp["data"]
                lib_ver = data["lib_version"]
                fw_ver = data["fw_version"]
                app_ver = data["app_version"]
                gw_addr = data["unicast_addr"]
                netkey = data["netkey"]
                nodes = data["nodes"]
                listener = data["listener"]
                scanning = data["scanning"]
                provisioning = data["provisioning"]
        return {
            "status": status,
            "init": init,
            "lib_ver": lib_ver,
            "fw_ver": fw_ver,
            "app_ver": app_ver,
            "gw_addr": gw_addr,
            "netkey": netkey,
            "nodes": nodes,
            "listener": listener,
            "scanning": scanning,
            "provisioning": provisioning
        }

    async def get_node_coverage(self):
        """Returns node coverage"""
        node_cvg = {}
        resp = self.gw_send_command(self.CMD_NODE_LIST, params={"cvg": True})
        if resp is not None:
            init = resp["success"]
            if init:
                for node in resp["data"]["node_list"]:
                    node_cvg[node["mac"]] = {}
                    if "coverage" in node:
                        node_cvg[node["mac"]] = node["coverage"]
        return {
            "coverage": node_cvg
        }

    async def get_pip_ver(self):
        """Returns TycheTools python programs versions"""
        ttgwlib = ttgwapp = bleconf = None
        retval, output = await self.shell("pip3 freeze")
        if retval == 0 and output is not None:
            for line in output.splitlines():
                param = line.split("==", 1)
                if param[0] == "ble-config-server":
                    bleconf = param[1].strip()
        return {
            "bleconf": bleconf
        }

    async def get_ble_status(self):
        """Returns ble_config_server status"""
        ble_status = None
        ble_pid = self.cat("/tmp/ble_config.pid")
        if len(ble_pid) != 0:
            ble_pid = ble_pid[0]
        retval, _ = await self.shell(f"ps -P {ble_pid}")
        ble_status = "Disabled"
        if retval == 0:
            ble_status = "Enabled"
        return ble_status

    async def get_gw_apps(self):
        """Returns gateway apps status"""
        backend = air_quality = snmp = csv = net_eng = mqtt = influx = None
        resp = self.gw_send_command(self.CMD_APP_LIST)
        if resp is not None and resp["success"] is True:
            data = resp["data"]
            backend = data["backend"]
            air_quality = data["air_quality"]
            snmp = data["snmp"]
            csv = data["csv"]
            net_eng = data["net_eng"]
            mqtt = data["mqtt"]
            influx = data["influx"]
        return {
            "backend": backend,
            "air_quality": air_quality,
            "snmp": snmp,
            "csv": csv,
            "net_eng": net_eng,
            "mqtt": mqtt,
            "influx": influx
        }

    async def get_ssh_tunnel(self):
        """Returns SSH tunnel info"""
        status = ssh_ip = ssh_port = None
        for line in self.cat("~/ssh_config"):
            param = line.split("=", 1)
            if param[0] == "ssh_ip":
                ssh_ip = param[1].strip()
            if param[0] == "ssh_port":
                ssh_port = int(param[1].strip())
        if ssh_ip:
            retval, _ = \
                await self.shell(
                    f"ssh -S /var/run/autossh.socket -O check {ssh_ip}")
            status = "Disabled"
            if retval == 0:
                status = "Enabled"
        return {
            "status": status,
            "ip": ssh_ip,
            "port": ssh_port
        }

    async def get_sys_info(self):
        """Returns system info"""
        cpu_num = cpu_perc = cpu_temp = filesys = disk_size = disk_avail = \
            ram_size = ram_avail = None
        retval, output = await self.shell("lscpu")
        if retval == 0 and output is not None:
            for line in output.splitlines():
                param = line.split(":", 1)
                if param[0] == "CPU(s)":
                    cpu_num = int(param[1].strip())
        cpu_perc = self.cat("/proc/loadavg")
        if len(cpu_perc) != 0:
            # Percentage last minute avg (0-CORES*100)
            cpu_perc = int(float(cpu_perc[0].split()[0]) * 100)
        cpu_temp = self.cat("/sys/class/thermal/thermal_zone0/temp")
        if len(cpu_temp) != 0:
            cpu_temp = int(int(cpu_temp[0].strip()) / 1000)
        retval, df_out = await self.shell(
            "df -h --output=source,size,avail -BM /home")
        if retval == 0 and df_out is not None:
            filesys = df_out.splitlines()[1].split()[0].strip()
            disk_size = int(df_out.splitlines()[1].split()[1].strip()[:-1])
            disk_avail = int(df_out.splitlines()[1].split()[2].strip()[:-1])
        for line in self.cat("/proc/meminfo"):
            param = line.split(":", 1)
            if param[0] == "MemTotal":
                ram_size = int(param[1].strip().split()[0])
            if param[0] == "MemAvailable":
                ram_avail = int(param[1].strip().split()[0])
        return {
            "cpu_num": cpu_num,
            "cpu_perc": cpu_perc,
            "cpu_temp": cpu_temp,
            "filesys": filesys,
            "disk_size": disk_size,
            "disk_available": disk_avail,
            "ram_size": ram_size,
            "ram_available": ram_avail
        }

    async def get_usb_devices(self):
        """Returns a list of the present USB devices"""
        usb_list = []
        retval, output = await self.shell("lsusb")
        if retval == 0 and output is not None:
            for line in output.splitlines():
                match = re.search("ID\s(\w+\:\w+)", line)
                if match:
                    usb_list.append(match.groups()[0])
        return usb_list

    def run(self):
        """Returns a full diagnostic"""
        devices, iface_en, iface_type = asyncio.run(self.get_ifaces())
        self.diagnosis["interfaces"] = []
        for dev in devices:
            iface = asyncio.run(self.get_iface_info(dev))
            interface = {}
            interface["name"] = dev
            interface["state"] = iface["state"]
            interface["type"] = iface["conntype"]
            interface["mac"] = iface["mac"]
            interface["ip"] = iface["ip"]
            self.diagnosis["interfaces"].append(interface)
        self.diagnosis["connection"]["connected"] = iface_en is not None
        if iface_en:
            self.diagnosis["connection"]["interface"] = iface_en
            iface_en_txrx = asyncio.run(self.get_iface_txrx(iface_en))
            self.diagnosis["connection"]["tx_bytes"] = iface_en_txrx["tx"]
            self.diagnosis["connection"]["rx_bytes"] = iface_en_txrx["rx"]
        if iface_type == "wifi":
            self.diagnosis["connection"]["wifi"]["status"] = "Enabled"
            wifi_info = asyncio.run(self.get_wifi_info())
            self.diagnosis["connection"]["wifi"]["ssid"] = wifi_info["ssid"]
            self.diagnosis["connection"]["wifi"]["passwd"] = wifi_info["passwd"]
            self.diagnosis["connection"]["wifi"]["signal"] = wifi_info["signal"]
        else:
            self.diagnosis["connection"]["wifi"]["status"] = "Disabled"
        if iface_type == "gsm":
            gsm_info = asyncio.run(self.get_gsm_info())
            self.diagnosis["connection"]["gsm"]["status"] = gsm_info["status"]
            self.diagnosis["connection"]["gsm"]["man"] = gsm_info["man"]
            self.diagnosis["connection"]["gsm"]["apn"] = gsm_info["apn"]
            self.diagnosis["connection"]["gsm"]["operator"] = \
                gsm_info["operator"]
            self.diagnosis["connection"]["gsm"]["tech"] = gsm_info["tech"]
            self.diagnosis["connection"]["gsm"]["signal"] = gsm_info["signal"]
        else:
            self.diagnosis["connection"]["wifi"]["status"] = "Disabled"
        ping = asyncio.run(self.get_ping())
        self.diagnosis["connection"]["ping"]["response"] = ping["response"]
        self.diagnosis["connection"]["ping"]["rtt_ms"] = ping["rtt"]
        self.diagnosis["general"]["hostname"] =  asyncio.run(self.get_hostname())
        self.diagnosis["general"]["localtime"] = asyncio.run(self.get_date())
        self.diagnosis["general"]["uptime_s"] = asyncio.run(self.get_uptime())
        ttversion = asyncio.run(self.get_ttversion())
        self.diagnosis["general"]["board"] = ttversion["board"]
        self.diagnosis["general"]["gitrev"] = ttversion["gitrev"]
        self.diagnosis["general"]["machine"] = ttversion["machine"]
        self.diagnosis["general"]["bt_mac"] = asyncio.run(self.get_bt_mac())
        self.diagnosis["general"]["device_id"] = None
        if self.diagnosis["general"]["bt_mac"]:
            self.diagnosis["general"]["device_id"] = \
                self.diagnosis["general"]["bt_mac"].lower().replace(":","")
        self.diagnosis["general"]["public_ip"] = asyncio.run(self.get_public_ip())
        gw_info = asyncio.run(self.get_gw_info())
        cvg_info = asyncio.run(self.get_node_coverage())
        self.diagnosis["proccesses"]["gateway"]["status"] = gw_info["status"]
        self.diagnosis["proccesses"]["gateway"]["init"] = gw_info["init"]
        self.diagnosis["proccesses"]["gateway"]["firmware"]["version"] = \
            gw_info["fw_ver"]
        self.diagnosis["proccesses"]["gateway"]["library"]["version"] = \
            gw_info["lib_ver"]
        self.diagnosis["proccesses"]["gateway"]["app"]["version"] = \
            gw_info["app_ver"]
        self.diagnosis["proccesses"]["gateway"]["gw_addr"] = gw_info["gw_addr"]
        self.diagnosis["proccesses"]["gateway"]["netkey"] = gw_info["netkey"]
        self.diagnosis["proccesses"]["gateway"]["nodes"] = gw_info["nodes"]
        self.diagnosis["proccesses"]["gateway"]["listener"] = \
            gw_info["listener"]
        self.diagnosis["proccesses"]["gateway"]["scanning"] = \
            gw_info["scanning"]
        self.diagnosis["proccesses"]["gateway"]["provisioning"] = \
            gw_info["provisioning"]
        self.diagnosis["proccesses"]["gateway"]["coverage"] = \
            cvg_info["coverage"]
        pip_ver = asyncio.run(self.get_pip_ver())
        self.diagnosis["proccesses"]["ble_config"]["version"] = \
            pip_ver["bleconf"]
        self.diagnosis["proccesses"]["ble_config"]["status"] = \
            asyncio.run(self.get_ble_status())
        gw_apps = asyncio.run(self.get_gw_apps())
        self.diagnosis["proccesses"]["gateway"]["apps"]["backend"] = \
            gw_apps["backend"]
        self.diagnosis["proccesses"]["gateway"]["apps"]["air_quality"] = \
            gw_apps["air_quality"]
        self.diagnosis["proccesses"]["gateway"]["apps"]["snmp"] = \
            gw_apps["snmp"]
        self.diagnosis["proccesses"]["gateway"]["apps"]["csv"] = gw_apps["csv"]
        self.diagnosis["proccesses"]["gateway"]["apps"]["net_eng"] = \
            gw_apps["net_eng"]
        self.diagnosis["proccesses"]["gateway"]["apps"]["mqtt"] = \
            gw_apps["mqtt"]
        self.diagnosis["proccesses"]["gateway"]["apps"]["influx"] = \
            gw_apps["influx"]
        ssh_tunnel = asyncio.run(self.get_ssh_tunnel())
        self.diagnosis["proccesses"]["ssh_tunnel"]["status"] = \
            ssh_tunnel["status"]
        self.diagnosis["proccesses"]["ssh_tunnel"]["ip"] = ssh_tunnel["ip"]
        self.diagnosis["proccesses"]["ssh_tunnel"]["port"] = ssh_tunnel["port"]
        sys_info = asyncio.run(self.get_sys_info())
        self.diagnosis["system"]["cpu_num"] = sys_info["cpu_num"]
        self.diagnosis["system"]["cpu_perc"] = sys_info["cpu_perc"]
        self.diagnosis["system"]["cpu_temp"] = sys_info["cpu_temp"]
        self.diagnosis["system"]["filesys"] = sys_info["filesys"]
        self.diagnosis["system"]["disk_size_mb"] = sys_info["disk_size"]
        self.diagnosis["system"]["disk_available_mb"] = \
            sys_info["disk_available"]
        self.diagnosis["system"]["ram_size_kb"] = sys_info["ram_size"]
        self.diagnosis["system"]["ram_available_kb"] = sys_info["ram_available"]
        self.diagnosis["system"]["usb_devices"] = \
            asyncio.run(self.get_usb_devices())
        return self.diagnosis

    def send(self):
        """Sends diagnostics to TycheTools backend"""
        self.ttapi.auth(self.user, self.password)
        diagnosis_url = \
            f"https://{self.client}-api.tychetools.com/data/gw-diagnostic/"
        body = {
                "device_id": self.diagnosis["general"]["device_id"],
                "data": self.diagnosis
        }
        rsp = self.ttapi.req_post(diagnosis_url, body)
        return rsp
