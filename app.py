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
    # Tailscale install requires root, so skip on Render free tier
    # Assume Tailscale is preinstalled manually or via a root VM
    # Just start tailscale node with auth key (no --advertise-exit-node)
    try:
        ts_up_cmd = f"tailscale up --authkey {TAILSCALE_AUTHKEY} --ssh"
        subprocess.run(ts_up_cmd, shell=True, check=True)
    except Exception as e:
        print(f"Cannot start Tailscale (Render free tier may lack root): {e}")
        ts_ip, public_ip = "N/A", "N/A"
        return ts_ip, public_ip

    # Get Tailscale and Public IP
    try:
        ts_ip = subprocess.check_output("tailscale ip -4", shell=True).decode().strip()
        public_ip = subprocess.check_output("curl -s ifconfig.me", shell=True).decode().strip()
    except Exception as e:
        ts_ip, public_ip = "N/A", "N/A"
        print(f"Failed to fetch IPs: {e}")

    print(f"Tailscale IP: {ts_ip}")
    print(f"Public IP: {public_ip}")

    # Telegram notification
    send_telegram(f"🚀 Tailscale Node Online\n🌐 Tailscale IP: {ts_ip}\n🌍 Public IP: {public_ip}\n⏱️ Active on Render!")

    return ts_ip, public_ip

def cleanup_tailscale(ts_ip, public_ip):
    # On Render, tailscale down may fail if no root, ignore errors
    try:
        subprocess.run("tailscale down", shell=True)
    except Exception as e:
        print(f"Cleanup failed (Render free tier): {e}")
    send_telegram(f"🛑 Tailscale Node Stopped\n🌐 Tailscale IP was: {ts_ip}\n🌍 Public IP was: {public_ip}")

# Health check / ping endpoint
@app.route("/")
def home():
    return jsonify({
        "status": "alive",
        "message": "✅ Tailscale Node is running!"
    })

# Optional ping endpoint
@app.route("/ping")
def ping():
    return jsonify({"status": "ok", "message": "🏓 Pong! Service is online."})

if __name__ == "__main__":
    ts_ip, public_ip = start_tailscale()
    try:
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
    finally:
        cleanup_tailscale(ts_ip, public_ip)
