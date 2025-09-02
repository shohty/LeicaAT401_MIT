import sys
import logging
import time
import threading
sys.path.insert(0, '/Users/shohtatakami/github/LeicaAT401_MIT')
from CESAPI.connection import Connection
from CESAPI.command import *

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CESAPI')
logger.setLevel(logging.DEBUG)

logging.getLogger('CESAPI.command').setLevel(logging.DEBUG)

def make_connection():
    global conn 
    conn = Connection()
    conn.connect(host='192.168.0.2', port=700)

def act_command():
    global command
    command = CommandSync(conn)

def print_status():
    sysstatus = command.GetSystemStatus()
    tracker_status = command.GetTrackerStatus()
    
    print("=== system status ===")
    print(f'Last Result Status : {sysstatus.lastResultStatus} (0=OK)')
    print(f'Tracker Processor Status : {sysstatus.trackerProcessorStatus} (4=CompensationSet)')
    print(f'Laser Status : {sysstatus.laserStatus} (3=Ready)')
    print(f'ADM Status : {sysstatus.admStatus} (2=Ready)')
    print(f'Weather Monitor Status : {sysstatus.weatherMonitorStatus} (2=ReadAndCalculate)')
    print(f'Tracker Status : {tracker_status.trackerStatus} (0=NotReady, 1=Busy, 2=Ready)')
    
    # Tracker Info
    try:
        info = command.GetTrackerInfo()
        print(f'Tracker Name : {info.cTrackerName.decode("utf-16").rstrip("\x00")}')
        print(f'Serial Number : {info.lSerialNumber}')
    except Exception as e:
        print(f'Tracker Info Error: {e}')

def test_movement_commands():
    try:
        print("\n=== Testing Movement Commands ===")
        
        # 小さな移動テスト
        print("Testing small movement...")
        command.PositionRelativeHV(0.001, 0.001)  # 0.001度移動
        print("Small movement completed")
        
        # 別の移動テスト
        print("Testing another movement...")
        command.PositionRelativeHV(-0.001, -0.001)  # 逆方向に移動
        print("Reverse movement completed")
        
    except Exception as e:
        print(f'Movement test error: {e}')

def test_continuous_movement():
    """連続移動テスト"""
    try:
        print("\n=== Testing Continuous Movement ===")
        print("Moving horizontally...")
        command.MoveHV(25, 0)  # 水平方向に移動
        time.sleep(2)  # 2秒間移動
        
        print("Moving vertically...")
        command.MoveHV(0, 25)  # 垂直方向に移動
        time.sleep(2)  # 2秒間移動
        
        print("Stopping movement...")
        command.MoveHV(0, 0)  # 停止
        print("Movement test completed")
        
    except Exception as e:
        print(f'Continuous movement error: {e}')
        # エラーが発生しても停止を試す
        try:
            command.MoveHV(0, 0)
        except:
            pass

def start_nivel_measurement():
    try:
        print("\n=== Starting Nivel Measurement ===")
        command.StartNivelMeasurement()
        print("Nivel measurement started successfully!")
        
        # 測定結果を表示
        if hasattr(command, 'nivel_measurement') and command.nivel_measurement:
            nivel = command.nivel_measurement
            print("=== Nivel Result ===")
            print(f'Nivel Status: {nivel.nivelStatus}')
            print(f'X Tilt: {nivel.dXTilt}')
            print(f'Y Tilt: {nivel.dYTilt}')
            print(f'Temperature: {nivel.dNivelTemperature}')
        else:
            print("No Nivel measurement data available")
    except Exception as e:
        print(f'Nivel measurement error: {e}')

if __name__=='__main__':
    try:
        make_connection()
        act_command()
        print_status()
        
        # 移動コマンドテスト（初期化なし）
        test_movement_commands()
        
        # 連続移動テスト
        test_continuous_movement()
        
        print("\n=== Initilizing Test ===")
        try:
            command.Initialize()
            print("Initilized Successfully !")
        except Exception as e:
            print(f'Initilization Error: {e}')
            print("Status 705 is not an error.")
            print("Check physical tracker status")
            
            # レベルセンサーの初期化を試す
            try:
                print("\n=== Trying InitializeNivel ===")
                command.InitializeNivel()
                print("Nivel initialized successfully!")
            except Exception as e2:
                print(f'Nivel initialization error: {e2}')
        
        # ニベル測定を実行
        start_nivel_measurement()
            
    except Exception as e:
        print(f'ERROR !! {e}')

