#!/usr/bin/env python3
"""
Leica Laser Tracker Mock Server
テスト用のモックサーバー
"""

import socket
import threading
import time
import struct
from CESAPI.packet import *

class MockLaserTrackerServer:
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.clients = []
        
    def start(self):
        """サーバーを開始"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        
        print(f"Mock Laser Tracker Server started on {self.host}:{self.port}")
        
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Client connected from {address}")
                self.clients.append(client_socket)
                
                # クライアントごとにスレッドを作成
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                    
    def handle_client(self, client_socket):
        """クライアントの接続を処理"""
        try:
            while self.running:
                # ヘッダーを受信
                header_data = client_socket.recv(12)
                if not header_data:
                    break
                    
                # パケットヘッダーを解析
                packet_header = PacketHeaderT()
                packet_header.unpack(header_data)
                
                # 残りのデータを受信
                remaining_data = client_socket.recv(packet_header.lPacketSize - 12)
                full_packet = header_data + remaining_data
                
                # パケットを解析
                packet_factory = PacketFactory()
                packet = packet_factory.packet(full_packet)
                
                print(f"Received command: {packet.packetInfo.command}")
                
                # コマンドに応じてレスポンスを送信
                response = self.create_response(packet)
                if response:
                    client_socket.sendall(response.pack())
                    
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
            if client_socket in self.clients:
                self.clients.remove(client_socket)
                
    def create_response(self, packet):
        """コマンドに応じたレスポンスを作成"""
        command = packet.packetInfo.command
        
        if command == ES_C_GetTrackerInfo:
            # GetTrackerInfoコマンドのレスポンス
            response = GetTrackerInfoRT()
            response.trackerType = 1  # AT401
            response.cTrackerName = b'AT401 Mock Tracker\x00' + b'\x00' * 15
            response.lSerialNumber = 12345
            response.lCompensationIdNumber = 1
            response.bHasADM = 1
            response.bHasOverviewCamera = 1
            response.bHasNivel = 1
            response.dNivelMountOffset = 0.0
            response.dMaxDistance = 160.0
            response.dMinDistance = 0.5
            response.iMaxDataRate = 1000
            response.iNumberOfFaces = 2
            response.dHzAngleRange = 240.0
            response.dVtAngleRange = 240.0
            response.accuracyModel = 0
            response.iMajLCPFirmwareVersion = 3
            response.iMinLCPFirmwareVersion = 6
            return response
            
        elif command == ES_C_GetSystemStatus:
            # GetSystemStatusコマンドのレスポンス
            response = GetSystemStatusRT()
            response.trackerProcessorStatus = ES_TPS_Initialized
            response.trackerStatus = ES_TS_Ready
            response.weatherMonitorStatus = ES_WMS_ReadAndCalculateRefractions
            response.bHasADM = 1
            response.bHasOverviewCamera = 1
            response.bHasNivel = 1
            response.bHasVideoCamera = 1
            return response
            
        elif command == ES_C_Initialize:
            # Initializeコマンドのレスポンス
            response = InitializeRT()
            response.status = ES_RS_AllOK
            return response
            
        else:
            # デフォルトの成功レスポンス
            response = BasicCommandRT()
            response.status = ES_RS_AllOK
            return response
            
    def stop(self):
        """サーバーを停止"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for client in self.clients:
            client.close()
        print("Mock Laser Tracker Server stopped")

if __name__ == "__main__":
    server = MockLaserTrackerServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop()
