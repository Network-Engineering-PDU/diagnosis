from datetime import datetime

from fastapi import FastAPI
import urllib3
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from model import Diagnosis

INFLUX_IP = "192.168.0.100"
# INFLUX_IP = "92.189.93.214" # Office public IP
INFLUX_TOKEN = "4rBM2s2QBIZOmYK_Gpo1tu-oDIcUuhV5B_AZxDWilVj9MMIa4o5v9rZrLL-J4bbVjDUrM0DgvsL7BpAE7CxQKQ=="
INFLUX_ORG = "tychetools"
INFLUX_BUCKET = "diagnosis"
INFLUX_POINT = "diagnosis"
INFLUX_TAG = "gateway"

client = InfluxDBClient(url=f"http://{INFLUX_IP}:8086", token=INFLUX_TOKEN)
write_api = client.write_api(write_options=SYNCHRONOUS)

def write(bt_mac, _type, value):
    """Write in InfluxDB"""
    point = Point(INFLUX_POINT)
    point.tag(INFLUX_TAG, bt_mac)
    point.field(_type, value)
    point.time(datetime.utcnow(), WritePrecision.MS)
    try:
        write_api.write(INFLUX_BUCKET, INFLUX_ORG, point)
        print(f"[{bt_mac}] {_type}: {value} written!")
    except urllib3.connection.NewConnectionError:
        print("Influx connection error")

app = FastAPI()

@app.post("/post-json")
async def post_json(diagnosis: Diagnosis):
    """Manage JSON"""
    print(diagnosis)
    if diagnosis.bt_mac is None:
        diagnosis.bt_mac = "unknown_device"
# General
    write(diagnosis.bt_mac, "hostname", diagnosis.hostname)
    write(diagnosis.bt_mac, "localtime", diagnosis.localtime)
    write(diagnosis.bt_mac, "uptime_s", diagnosis.uptime_s)
    write(diagnosis.bt_mac, "board", diagnosis.board)
    write(diagnosis.bt_mac, "gitrev", diagnosis.gitrev)
    write(diagnosis.bt_mac, "machine", diagnosis.machine)
    write(diagnosis.bt_mac, "public_ip", diagnosis.public_ip)
# Hardware
# Proccesses
    write(diagnosis.bt_mac, "gw_status", diagnosis.proccesses.gateway.status)
    write(diagnosis.bt_mac, "gw_init", diagnosis.proccesses.gateway.init)
    write(diagnosis.bt_mac, "gw_gw_addr", diagnosis.proccesses.gateway.gw_addr)
    write(diagnosis.bt_mac, "gw_netkey", diagnosis.proccesses.gateway.netkey)
    write(diagnosis.bt_mac, "gw_nodes", diagnosis.proccesses.gateway.nodes)
    write(diagnosis.bt_mac, "gw_scanning", diagnosis.proccesses.gateway.scanning)
    write(diagnosis.bt_mac, "gw_provisioning", diagnosis.proccesses.gateway.provisioning)
    write(diagnosis.bt_mac, "gw_fw_ver", diagnosis.proccesses.gateway.firmware.version)
    write(diagnosis.bt_mac, "gw_lib_ver", diagnosis.proccesses.gateway.library.version)
    write(diagnosis.bt_mac, "gw_app_ver", diagnosis.proccesses.gateway.app.version)
    write(diagnosis.bt_mac, "gw_apps_backend", diagnosis.proccesses.gateway.apps.backend)
    write(diagnosis.bt_mac, "gw_apps_snmp", diagnosis.proccesses.gateway.apps.snmp)
    write(diagnosis.bt_mac, "gw_apps_mqtt", diagnosis.proccesses.gateway.apps.mqtt)
    write(diagnosis.bt_mac, "gw_apps_influx", diagnosis.proccesses.gateway.apps.influx)
    write(diagnosis.bt_mac, "gw_apps_csv", diagnosis.proccesses.gateway.apps.csv)
    write(diagnosis.bt_mac, "gw_apps_net_eng", diagnosis.proccesses.gateway.apps.net_eng)
    write(diagnosis.bt_mac, "gw_apps_air_quality", diagnosis.proccesses.gateway.apps.air_quality)
    write(diagnosis.bt_mac, "ble_status", diagnosis.proccesses.ble_config.status)
    write(diagnosis.bt_mac, "ble_ver", diagnosis.proccesses.ble_config.version)
    write(diagnosis.bt_mac, "ssh_tunnel_status", diagnosis.proccesses.ssh_tunnel.status)
    write(diagnosis.bt_mac, "ssh_tunnel_ip", diagnosis.proccesses.ssh_tunnel.ip)
    write(diagnosis.bt_mac, "ssh_tunnel_port", diagnosis.proccesses.ssh_tunnel.port)
# Interfaces
    for iface in diagnosis.interfaces:
        write(diagnosis.bt_mac, f"{iface.name}_type", iface.type)
        write(diagnosis.bt_mac, f"{iface.name}_mac", iface.mac)
        write(diagnosis.bt_mac, f"{iface.name}_state", iface.state)
        write(diagnosis.bt_mac, f"{iface.name}_ip", iface.ip)
# Connection
    write(diagnosis.bt_mac, "connected", diagnosis.connection.connected)
    write(diagnosis.bt_mac, "interface", diagnosis.connection.interface)
    write(diagnosis.bt_mac, "tx_bytes", diagnosis.connection.tx_bytes)
    write(diagnosis.bt_mac, "rx_bytes", diagnosis.connection.rx_bytes)
    write(diagnosis.bt_mac, "ping_response", diagnosis.connection.ping.response)
    write(diagnosis.bt_mac, "ping_rtt_ms", diagnosis.connection.ping.rtt_ms)
    write(diagnosis.bt_mac, "wifi_status", diagnosis.connection.wifi.status)
    write(diagnosis.bt_mac, "wifi_ssid", diagnosis.connection.wifi.ssid)
    write(diagnosis.bt_mac, "wifi_passwd", diagnosis.connection.wifi.passwd)
    write(diagnosis.bt_mac, "wifi_signal", diagnosis.connection.wifi.signal)
    write(diagnosis.bt_mac, "gsm_status", diagnosis.connection.gsm.status)
    write(diagnosis.bt_mac, "gsm_man", diagnosis.connection.gsm.man)
    write(diagnosis.bt_mac, "gsm_apn", diagnosis.connection.gsm.apn)
    write(diagnosis.bt_mac, "gsm_operator", diagnosis.connection.gsm.operator)
    write(diagnosis.bt_mac, "gsm_tech", diagnosis.connection.gsm.tech)
    write(diagnosis.bt_mac, "gsm_signal", diagnosis.connection.gsm.signal)
# System
    write(diagnosis.bt_mac, "cpu_num", diagnosis.system.cpu_num)
    write(diagnosis.bt_mac, "cpu_perc", diagnosis.system.cpu_perc)
    write(diagnosis.bt_mac, "cpu_temp", diagnosis.system.cpu_temp)
    write(diagnosis.bt_mac, "filesys", diagnosis.system.filesys)
    write(diagnosis.bt_mac, "disk_size_mb", diagnosis.system.disk_size_mb)
    write(diagnosis.bt_mac, "disk_available_mb", diagnosis.system.disk_available_mb)
    write(diagnosis.bt_mac, "ram_size_kb", diagnosis.system.ram_size_kb)
    write(diagnosis.bt_mac, "ram_available_kb", diagnosis.system.ram_available_kb)
    write(diagnosis.bt_mac, "usb_devices", str(diagnosis.system.usb_devices))

    return diagnosis
