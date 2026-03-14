#!/usr/bin/env python3
"""
CTRL//HUB — Pi Stats Server
Serves live system stats as JSON on http://localhost:5050/stats
Run with: python3 stats_server.py &
"""
import json
import socket
import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
def get_cpu_usage():
"""Read CPU usage by sampling /proc/stat over 200ms."""
def read_stat():
with open('/proc/stat') as f:
line = f.readline()
vals = list(map(int, line.split()[1:8]))
idle = vals[3]
total = sum(vals)
return idle, total
idle1, total1 = read_stat()
time.sleep(0.2)
idle2, total2 = read_stat()
idle_diff = idle2 - idle1
total_diff = total2 - total1
if total_diff == 0:
return 0.0
return round((1 - idle_diff / total_diff) * 100, 1)
def get_ram_usage():
"""Return RAM usage percentage."""
with open('/proc/meminfo') as f:
lines = f.readlines()
info = {}
for line in lines:
parts = line.split()
if len(parts) >= 2:
info[parts[0].rstrip(':')] = int(parts[1])
total = info.get('MemTotal', 1)
free = info.get('MemFree', 0)
buffers = info.get('Buffers', 0)
cached = info.get('Cached', 0)
used = total - free - buffers - cached
return round((used / total) * 100, 1)
def get_temperature():
"""Read CPU temperature from Pi thermal zone."""
try:
with open('/sys/class/thermal/thermal_zone0/temp') as f:
return round(int(f.read().strip()) / 1000, 1)
except:
return 0.0
def get_cpu_freq():
"""Read current CPU frequency in MHz."""
try:
with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq') as f:
return round(int(f.read().strip()) / 1000)
except:
try:
except:
# Fallback for Pi Zero
with open('/sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq') as f:
return round(int(f.read().strip()) / 1000)
return 0
def get_ip():
try:
"""Get the Pi's local IP address."""
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
ip = s.getsockname()[0]
s.close()
return ip
except:
return '—'
def get_uptime():
"""Return uptime in seconds."""
try:
with open('/proc/uptime') as f:
return int(float(f.read().split()[0]))
except:
return 0
class StatsHandler(BaseHTTPRequestHandler):
def do_GET(self):
if self.path == '/stats':
stats = {
'cpu': get_cpu_usage(),
'ram': get_ram_usage(),
'temp': get_temperature(),
'freq': get_cpu_freq(),
'ip': get_ip(),
'uptime': get_uptime(),
}
body = json.dumps(stats).encode()
self.send_response(200)
self.send_header('Content-Type', 'application/json')
self.send_header('Content-Length', len(body))
# Allow dashboard to fetch from file:// origin
self.send_header('Access-Control-Allow-Origin', '*')
self.end_headers()
self.wfile.write(body)
else:
self.send_response(404)
self.end_headers()
def log_message(self, format, *args):
# Suppress request logs to keep terminal clean
pass
if __name__ == '__main__':
server = HTTPServer(('localhost', 5050), StatsHandler)
print('Pi stats server running on http://localhost:5050/stats')
print('Press Ctrl+C to stop.')
try:
server.serve_forever()
except KeyboardInterrupt:
print('\nStopped.')