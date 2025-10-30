#!/usr/bin/env python3
"""
Leica Laser Trackerのコマンドバイナリデータを表示するスクリプト
接続なしで実行可能
"""

import sys
import os
import struct

# CESAPIのパスを追加
sys.path.insert(0, '/Users/shohtatakami/github/LeicaAT401_MIT')
from CESAPI.packet import *

def show_command_binary(command_name, packet_class):
    """指定されたコマンドのバイナリデータを表示"""
    try:
        print(f"\n=== {command_name} Binary Data Analysis ===")
        
        # パケットを作成
        packet = packet_class()
        
        # パケットをバイナリに変換
        binary_data = packet.pack()
        
        print(f"Packet size: {len(binary_data)} bytes")
        print(f"Binary data (hex): {binary_data.hex()}")
        print(f"Binary data (bytes): {binary_data}")
        
        # 構造を解析して表示
        print(f"\n=== {command_name} Packet Structure ===")
        
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
            print(f"  command: {command_value}")
        
        # 追加データがある場合
        if len(binary_data) > 12:
            extra_data = binary_data[12:]
            print(f"Extra data ({len(extra_data)} bytes): {extra_data.hex()}")
        
        print(f"✓ {command_name} analysis completed")
        return binary_data
        
    except Exception as e:
        print(f"Error analyzing {command_name}: {e}")
        return None

def main():
    """メイン関数 - 複数のコマンドを表示"""
    print("=== Leica Laser Tracker Command Binary Analysis ===")
    print("接続なしでコマンドのバイナリデータを表示します\n")
    
    # よく使われるコマンドのリスト
    commands = [
        ("GetTrackerInfo", GetTrackerInfoCT),
        ("GetSystemStatus", GetSystemStatusCT),
        ("GetTrackerStatus", GetTrackerStatusCT),
        ("GetUnits", GetUnitsCT),
        ("GetMeasurementMode", GetMeasurementModeCT),
        ("GetSystemSettings", GetSystemSettingsCT),
        ("GetEnvironmentParams", GetEnvironmentParamsCT),
        ("GetReflector", GetReflectorCT),
        ("GetReflectors", GetReflectorsCT),
        ("Initialize", InitializeCT),
        ("Park", ParkCT),
        ("StartMeasurement", StartMeasurementCT),
    ]
    
    # 各コマンドのバイナリを表示
    for command_name, packet_class in commands:
        show_command_binary(command_name, packet_class)
        print("-" * 60)

if __name__ == "__main__":
    main()
