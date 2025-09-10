#!/usr/bin/env python3
"""
WiFi接続機器スキャナー
現在のWiFiネットワークに接続している機器を検出します
"""

import subprocess
import socket
import threading
import ipaddress
import platform
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class WiFiScanner:
    def __init__(self):
        self.system = platform.system()
        self.devices = []
    
    def get_network_info(self):
        """現在のネットワーク情報を取得"""
        try:
            if self.system == "Darwin":  # macOS
                result = subprocess.run(['route', '-n', 'get', 'default'], 
                                      capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'gateway:' in line:
                        gateway = line.split(':')[1].strip()
                        break
                
                # ネットワーク範囲を推定
                result = subprocess.run(['ifconfig'], capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'inet ' in line and '127.0.0.1' not in line:
                        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match:
                            ip = ip_match.group(1)
                            # /24ネットワークを仮定
                            network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
                            return str(network), gateway
            
            elif self.system == "Linux":
                result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                      capture_output=True, text=True)
                gateway = result.stdout.split()[2]
                
                result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
                ip = result.stdout.strip().split()[0]
                network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
                return str(network), gateway
            
            elif self.system == "Windows":
                result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'Default Gateway' in line:
                        gateway = line.split(':')[1].strip()
                        # 前の行からIPアドレスを取得
                        for j in range(i-5, i):
                            if 'IPv4 Address' in lines[j]:
                                ip = lines[j].split(':')[1].strip()
                                network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
                                return str(network), gateway
        
        except Exception as e:
            print(f"ネットワーク情報の取得に失敗: {e}")
            return None, None
    
    def ping_host(self, ip):
        """ホストにpingを送信"""
        try:
            if self.system == "Windows":
                result = subprocess.run(['ping', '-n', '1', '-w', '1000', ip], 
                                      capture_output=True, text=True, timeout=2)
            else:
                result = subprocess.run(['ping', '-c', '1', '-W', '1', ip], 
                                      capture_output=True, text=True, timeout=2)
            
            return result.returncode == 0
        except:
            return False
    
    def get_hostname(self, ip):
        """IPアドレスからホスト名を取得"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return "Unknown"
    
    def get_mac_address(self, ip):
        """ARPテーブルからMACアドレスを取得"""
        try:
            if self.system == "Windows":
                result = subprocess.run(['arp', '-a', ip], capture_output=True, text=True)
            else:
                result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True)
            
            # MACアドレスを抽出
            mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', result.stdout)
            if mac_match:
                return mac_match.group(0)
        except:
            pass
        return "Unknown"
    
    def scan_network(self, network_range, max_threads=50):
        """ネットワークをスキャンして接続機器を検出"""
        print(f"ネットワーク {network_range} をスキャン中...")
        
        network = ipaddress.IPv4Network(network_range)
        active_hosts = []
        
        # 並列でpingを実行
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_ip = {executor.submit(self.ping_host, str(ip)): str(ip) 
                           for ip in network.hosts()}
            
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    if future.result():
                        active_hosts.append(ip)
                        print(f"✓ {ip} - 応答あり")
                except Exception as e:
                    pass
        
        # 詳細情報を取得
        print("\n詳細情報を取得中...")
        devices = []
        for ip in active_hosts:
            hostname = self.get_hostname(ip)
            mac = self.get_mac_address(ip)
            
            device_info = {
                'ip': ip,
                'hostname': hostname,
                'mac': mac,
                'status': 'Online'
            }
            devices.append(device_info)
        
        return devices
    
    def print_results(self, devices):
        """結果を表示"""
        print("\n" + "="*60)
        print("WiFi接続機器一覧")
        print("="*60)
        print(f"{'IP Address':<15} {'Hostname':<25} {'MAC Address':<18} {'Status'}")
        print("-"*60)
        
        for device in devices:
            print(f"{device['ip']:<15} {device['hostname']:<25} {device['mac']:<18} {device['status']}")
        
        print(f"\n合計 {len(devices)} 台の機器が検出されました")

def main():
    scanner = WiFiScanner()
    
    # ネットワーク情報を取得
    network_range, gateway = scanner.get_network_info()
    
    if not network_range:
        print("ネットワーク情報の取得に失敗しました")
        return
    
    print(f"ゲートウェイ: {gateway}")
    print(f"スキャン範囲: {network_range}")
    
    # ネットワークをスキャン
    devices = scanner.scan_network(network_range)
    
    # 結果を表示
    scanner.print_results(devices)

if __name__ == "__main__":
    main()




