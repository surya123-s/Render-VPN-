import os
import subprocess
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# Environment Variables
TAILSCALE_AUTHKEY = os.getenv("TAILSCALE_AUTHKEY")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def send_telegram(message):
    if TG_BOT_TOKEN and TG_CHAT_ID:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TG_CHAT_ID, "text": message}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Failed to send Telegram message: {e}")

def start_tailscale():
    # Install Tailscale
    subprocess.run("curl -fsSL https://tailscale.com/install.sh | sh", shell=True, check=True)

    # Enable IP forwarding
    subprocess.run("sudo sysctl -w net.ipv4.ip_forward=1", shell=True, check=True)
    subprocess.run("sudo sysctl -w net.ipv6.conf.all.forwarding=1", shell=True, check=True)

    # Start Tailscale as exit node
    subprocess.run(f"sudo tailscale up --authkey {TAILSCALE_AUTHKEY} --ssh --advertise-exit-node", shell=True, check=True)

    # Get Tailscale and Public IP
    ts_ip = subprocess.check_output("sudo tailscale ip -4", shell=True).decode().strip()
    public_ip = subprocess.check_output("curl -s ifconfig.me", shell=True).decode().strip()

    print(f"Tailscale IP: {ts_ip}")
    print(f"Public IP: {public_ip}")

    # Telegram notification
    send_telegram(f"🚀 Tailscale Exit Node Online\n🌐 Tailscale IP: {ts_ip}\n🌍 Public IP: {public_ip}\n⏱️ Active on Render!")

    return ts_ip, public_ip

def cleanup_tailscale(ts_ip, public_ip):
    subprocess.run("sudo tailscale down", shell=True)
    send_telegram(f"🛑 Tailscale Exit Node Stopped\n🌐 Tailscale IP was: {ts_ip}\n🌍 Public IP was: {public_ip}")

# Health check / ping endpoint
@app.route("/")
def home():
    return jsonify({
        "status": "alive",
        "message": "✅ Tailscale Exit Node is running!"
    })

# Optional ping endpoint
@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "🏓 Pong! Service is online."})

if __name__ == "__main__":
    ts_ip, public_ip = start_tailscale()
    try:
        app.run(host="0.0.0.0", port=10000)
    finally:
        cleanup_tailscale(ts_ip, public_ip)
