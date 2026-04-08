import psutil
import requests
import time
import socket
import os

# Requirements:
# pip install psutil requests
# Windows only: pip install wmi

# Configuration
PI_URL = "http://pimonitor.local:8000"
INTERVAL = 5  # seconds between updates

def get_machine_name():
    return socket.gethostname()

def get_cpu_temp():
    if os.name == "nt":  # Use wmi on windows to get cpu temp.
        try:
            import wmi
            w = wmi.WMI(namespace="root\\wmi")
            temps = w.MSAcpi_ThermalZoneTemperature()
            return round(temps[0].CurrentTemperature / 10 - 273.15, 1)
        except:
            return None

    else:  # Open the temp file to get cpu temp on Linux/Mac
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return round(int(f.read()) / 1000, 1)
        except:
            return None

def collect_stats():
    ram = psutil.virtual_memory()
    disk_path = "C:\\" if os.name == "nt" else "/"
    disk = psutil.disk_usage(disk_path)
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_temp": get_cpu_temp(),
        "ram_used": round(ram.used / 1024**2),
        "ram_total": round(ram.total / 1024**2),
        "ram_percent": int(ram.percent),
        "disk_used": round(disk.used / 1024**3, 1),
        "disk_total": round(disk.total / 1024**3, 1),
    }

def send_stats(stats):
    machine_name = get_machine_name()
    try:
        requests.post(
            f"{PI_URL}/api/machines/{machine_name}/stats",
            json=stats,
            timeout=5
        )
        print(f"Sent stats for {machine_name}")
    except Exception as e:
        print(f"Failed to send stats: {e}")

if __name__ == "__main__":
    print(f"Starting agent for {get_machine_name()}")
    while True:
        stats = collect_stats()
        send_stats(stats)
        time.sleep(INTERVAL)
