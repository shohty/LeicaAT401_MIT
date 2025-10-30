#!/usr/bin/env python3
"""
GetTrackerInfoで送信されるバイナリデータを表示するスクリプト
接続なしで実行可能
"""

import sys
import os
import struct

# CESAPIのパスを追加
sys.path.insert(0, '/Users/shohtatakami/github/LeicaAT401_MIT')
from CESAPI.packet import GetTrackerInfoCT

def show_binary_data():
    """GetTrackerInfoで送信されるバイナリデータを表示"""
    try:
        print("=== GetTrackerInfo Binary Data Analysis ===")
        
        # GetTrackerInfoCTパケットを作成
        packet = GetTrackerInfoCT()
        
        # パケットをバイナリに変換
        binary_data = packet.pack()
        
        print(f"Packet size: {len(binary_data)} bytes")
        print(f"Binary data (hex): {binary_data.hex()}")
        print(f"Binary data (bytes): {binary_data}")
        
        # 構造を解析して表示
        print("\n=== Packet Structure Analysis ===")
        
        # パケットヘッダー部分（8バイト）
        if len(binary_data) >= 8:
            header_data = binary_data[:8]
            print(f"Header (8 bytes): {header_data.hex()}")
            
            # struct.unpackで解析
            lPacketSize, packet_type = struct.unpack('<iI', header_data)
            print(f"  lPacketSize: {lPacketSize}")
            print(f"  type: {packet_type} (ES_DT_Command = 0)")
        
        # コマンド部分（4バイト）
        if len(binary_data) >= 12:
            command_data = binary_data[8:12]
            print(f"Command (4 bytes): {command_data.hex()}")
            
            command_value = struct.unpack('<I', command_data)[0]
            print(f"  command: {command_value} (ES_C_GetTrackerInfo = 132)")
        
        print("\n=== Summary ===")
        print(f"Total packet: {len(binary_data)} bytes")
        print(f"Hex representation: {binary_data.hex()}")
        print("✓ Binary data analysis completed")
        
        return binary_data
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    show_binary_data()
