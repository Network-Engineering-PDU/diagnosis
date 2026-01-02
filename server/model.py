from typing import Union, List
from pydantic import BaseModel

class Hardware(BaseModel):
    hw_version: Union[str, None]
    enclosure: Union[str, None]
    shield_present: Union[bool, None]
    leds: Union[str, None]

class GwFirmware(BaseModel):
    version: Union[str, None]

class GwLibrary(BaseModel):
    version: Union[str, None]

class GwApp(BaseModel):
    version: Union[str, None]

class GwApps(BaseModel):
    backend: Union[str, None]
    snmp: Union[str, None]
    mqtt: Union[str, None]
    influx: Union[str, None]
    csv: Union[str, None]
    net_eng: Union[str, None]
    air_quality: Union[str, None]

class Gateway(BaseModel):
    status: Union[str, None]
    init: Union[bool, None]
    gw_addr: Union[int, None]
    netkey: Union[str, None]
    nodes: Union[int, None]
    listener: Union[bool, None]
    scanning: Union[bool, None]
    provisioning: Union[bool, None]
    firmware: GwFirmware
    library: GwLibrary
    app: GwApp
    apps: GwApps

class BleConfig(BaseModel):
    status: Union[str, None]
    version: Union[str, None]

class SshTunnel(BaseModel):
    status: Union[str, None]
    ip: Union[str, None]
    port: Union[int, None]

class Proccesses(BaseModel):
    gateway: Gateway
    ble_config: BleConfig
    ssh_tunnel: SshTunnel

class Interfaces(BaseModel):
    name: Union[str, None]
    type: Union[str, None]
    mac: Union[str, None]
    state: Union[str, None]
    ip: Union[str, None]

class ConnPing(BaseModel):
    response: Union[bool, None]
    rtt_ms: Union[float, None]

class ConnWifi(BaseModel):
    status: Union[str, None]
    ssid: Union[str, None]
    passwd: Union[str, None]
    signal: Union[int, None]

class ConnGsm(BaseModel):
    status: Union[str, None]
    man: Union[str, None]
    apn: Union[str, None]
    operator: Union[str, None]
    tech: Union[str, None]
    signal: Union[int, None]

class Connection(BaseModel):
    connected: Union[bool, None]
    interface: Union[str, None]
    tx_bytes: Union[int, None]
    rx_bytes: Union[int, None]
    ping: ConnPing
    wifi: ConnWifi
    gsm: ConnGsm

class System(BaseModel):
    cpu_num: Union[int, None]
    cpu_perc: Union[int, None]
    cpu_temp: Union[int, None]
    filesys: Union[str, None]
    disk_size_mb: Union[int, None]
    disk_available_mb: Union[int, None]
    ram_size_kb: Union[int, None]
    ram_available_kb: Union[int, None]
    usb_devices: List[str]

class Diagnosis(BaseModel):
    hostname: Union[str, None]
    localtime: Union[str, None]
    uptime_s: Union[int, None]
    board: Union[str, None]
    gitrev: Union[str, None]
    machine: Union[str, None]
    bt_mac: Union[str, None]
    public_ip: Union[str, None]
    hardware: Hardware
    proccesses: Proccesses
    interfaces: List[Interfaces]
    connection: Connection
    system: System