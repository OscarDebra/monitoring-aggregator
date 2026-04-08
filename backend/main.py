from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psutil
import sqlite3
import json
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect("stats.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS machine_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            stats TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup():
    init_db()

class MachineStats(BaseModel):
    cpu_percent: float
    cpu_temp: Optional[float]
    ram_used: int
    ram_total: int
    ram_percent: float
    disk_used: float
    disk_total: float

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read()) / 1000, 1)
    except:
        return None

@app.get("/api/stats")
def get_stats():
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_temp": get_cpu_temp(),
        "ram_used": round(ram.used / 1024**2),
        "ram_total": round(ram.total / 1024**2),
        "ram_percent": int(ram.percent),
        "disk_used": round(disk.used / 1024**3, 1),
        "disk_total": round(disk.total / 1024**3, 1),
    }

@app.post("/api/machines/{machine_name}/stats")
def receive_stats(machine_name: str, stats: MachineStats):
    conn = get_db()
    conn.execute(
        "INSERT INTO machine_stats (machine_name, timestamp, stats) VALUES (?, ?, ?)",
        (machine_name, datetime.now(timezone.utc).isoformat(), json.dumps(stats.dict()))
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/machines")
def get_machines():
    conn = get_db()
    rows = conn.execute("""
        SELECT machine_name, timestamp, stats
        FROM machine_stats
        WHERE id IN (
            SELECT MAX(id) FROM machine_stats GROUP BY machine_name
        )
    """).fetchall()
    conn.close()

    machines = []
    for row in rows:
        last_seen = datetime.fromisoformat(row["timestamp"])
        now = datetime.now(timezone.utc)
        online = (now - last_seen).seconds < 30
        machines.append({
            "machine_name": row["machine_name"],
            "timestamp": row["timestamp"],
            "online": online,
            **json.loads(row["stats"])
        })
    return machines