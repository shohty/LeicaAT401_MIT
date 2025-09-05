import sys
import logging
import time
import threading
sys.path.insert(0, '/Users/shohtatakami/github/LeicaAT401_MIT')
from CESAPI.connection import Connection
from CESAPI.command import *
from CESAPI.packet import *

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('CESAPI')
logger.setLevel(logging.DEBUG)

logging.getLogger('CESAPI.command').setLevel(logging.DEBUG)
##connection->sync_commandで一回check_connection
##うまくいかない場合はdisconnect_from_trackerで少し待ってからもう一度同じ流れ
##それでもダメな場合はトラッカー再起動

def check_connection():
    try:
        print("=== Checking Connection ===")
        print("1. Checking connection...")
        response = command.GetTrackerInfo()#簡単なコマンドを送って接続を確認
        print(f"new status object: {response}")
        trackername = response.cTrackerName
        print(f"Tracker Name: {trackername.decode('utf-16').rstrip('\x00')}")
        print("✓ Connection check successful")
        return True
    except Exception as e:
        print(f"Failed to check connection: {e}")
        return False
def disconnect_from_tracker():
    """レーザートラッカーとの接続を切断"""
    try:
        print("=== Disconnecting from Laser Tracker ===")
        
        # 接続を切断
        conn.disconnect()
        print("✓ Successfully disconnected from laser tracker")
        return True
        
    except Exception as e:
        print(f"Failed to disconnect: {e}")
        return False


def revive_connection():
    try:
        print("=== Reviving Connection ===")
        try:
            conn.close()
            print(f"Closed old connection")
        except:
            pass
        print(f"creating new connection")
        connection()
        sync_command()
        
        if check_connection():
            print(f"✓ Connection revived successfully")
            return True
        else:
            print(f"✗ Connection revival failed")
            return False
    except Exception as e:
        print(f"Failed to revive connection: {e}")
        return False
def initialize():
    try:
        print("=== Initializing ===")
        command.Initialize()
        print(f"✓ Initialization successful")
        return True
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return False
def connection():
    global conn 
    conn = Connection()
    if conn.connect(host='192.168.0.2', port=700):
        print("✓ Connection successful")
        return True
    else:
        print("✗ Connection failed")
        return False

def sync_command():
    global command
    print("=== Creating Command Object ===")
    print(f"Connection object: {conn}")
    command = CommandSync(conn)
    print(f"Command object created: {command}")
    print("✓ Command object ready")

def set_units():
    units = SystemUnitsDataT()
    # 各単位を設定
    units.lenUnitType = ES_LU_Millimeter      # 長さ単位: ミリメートル
    units.angUnitType = ES_AU_Degree          # 角度単位: 度
    units.tempUnitType = ES_TU_Fahrenheit        # 温度単位: 摂氏
    units.pressUnitType = ES_PU_InHg       # 圧力単位: インチ水銀柱
    units.humUnitType = ES_HU_RH              # 湿度単位: 相対湿度
    command.SetUnits(units)
    print(f'Units set successfully')
def get_units():
    units = command.GetUnits()
    print(f'Length Unit Type: {units.unitsSettings.lenUnitType}')                   # 単位を設定
    print(f'Angle Unit Type: {units.unitsSettings.angUnitType}')
    print(f'Temperature Unit Type: {units.unitsSettings.tempUnitType}')
    print(f'Pressure Unit Type: {units.unitsSettings.pressUnitType}')
    print(f'Humidity Unit Type: {units.unitsSettings.humUnitType}')
def get_environment_info():
    """環境パラメータを取得して出力"""
    try:
        # 環境パラメータを取得
        env_params = command.GetEnvironmentParams()
        
        print("\n=== Current Environment Parameters ===")
        print(f"Temperature: {env_params.environmentData.dTemperature}°F")
        print(f"Pressure: {env_params.environmentData.dPressure} kPa")
        print(f"Humidity: {env_params.environmentData.dHumidity}%")
        return env_params
        
    except Exception as e:
        print(f"Error getting environment params: {e}")
        return None
def check_system_settings():
    """システム設定を確認"""
    try:
        print("=== Checking System Settings ===")
        settings_response = command.GetSystemSettings()
        settings = settings_response.systemSettings
        print(f"Weather Monitor Status: {settings.weatherMonitorStatus}")
        print(f"Apply Transformation: {settings.bApplyTransformationParams}")
        print(f"Apply Station Orientation: {settings.bApplyStationOrientationParams}")
        print(f"Keep Last Position: {settings.bKeepLastPosition}")
        print(f"Send Unsolicited Messages: {settings.bSendUnsolicitedMessages}")
        print(f"Send Reflector Position Data: {settings.bSendReflectorPositionData}")
        print(f"Try Measurement Mode: {settings.bTryMeasurementMode}")
        print(f"Has Nivel: {settings.bHasNivel}")
        print(f"Has Video Camera: {settings.bHasVideoCamera}")
        return settings
    except Exception as e:
        print(f"Failed to get system settings: {e}")
        return None

def set_envparams():
    """環境パラメータを設定（競合を避ける方法）"""
    try:
        print("=== Setting Environment Parameters ===")
        
        # 1. システム設定を確認
        settings = check_system_settings()
        if settings and settings.weatherMonitorStatus != ES_WMS_NotConnected:
            print("⚠️ Weather monitor is connected. Manual environment setting may conflict.")
            print("Consider setting weather monitor to 'Not Connected' first.")
        
        # 2. 現在の環境データを取得
        current_env_response = command.GetEnvironmentParams()
        current_env = current_env_response.environmentData
        print(f"Current - Temperature: {current_env.dTemperature:.2f} °F")
        print(f"Current - Pressure: {current_env.dPressure:.2f} ")
        print(f"Current - Humidity: {current_env.dHumidity:.2f} %")
        
        # 3. 新しい環境データオブジェクトを作成（範囲内の値に修正）
        new_env = EnvironmentDataT()
        new_env.dTemperature = current_env.dTemperature  # 温度はそのまま
        
        # 圧力を適切な範囲に修正
        if current_env.dPressure < 90.0 or current_env.dPressure > 110.0:
            new_env.dPressure = 101.325  # 標準大気圧
            print(f"⚠️ Pressure out of range, setting to standard: {new_env.dPressure} kPa")
        else:
            new_env.dPressure = current_env.dPressure
            
        new_env.dHumidity = current_env.dHumidity  # 湿度はそのまま
        
        print(f"Setting - Temperature: {new_env.dTemperature:.2f} °F")
        print(f"Setting - Pressure: {new_env.dPressure:.2f} inHg")
        print(f"Setting - Humidity: {new_env.dHumidity:.2f} %")
        
        # 4. 環境パラメータを設定
        command.SetEnvironmentParams(new_env)
        print("✓ Environment params set successfully")
        return True
        
    except Exception as e:
        print(f"Failed to set environment params: {e}")
        return False

def disable_weather_monitor():
    """気象モニターを無効化して環境パラメータを手動設定可能にする"""
    try:
        print("=== Disabling Weather Monitor ===")
        
        # システム設定を取得
        settings_response = command.GetSystemSettings()
        settings = settings_response.systemSettings
        
        # 気象モニターを無効化
        settings.weatherMonitorStatus = ES_WMS_NotConnected
        
        # システム設定を更新
        command.SetSystemSettings(settings)
        print("✓ Weather monitor disabled")
        return True
        
    except Exception as e:
        print(f"Failed to disable weather monitor: {e}")
        return False
def initialization():
    """段階的な初期化"""
    try:
        print("=== Gradual Initialization ===")
        
        # 1. システム状態を確認
        print("1. Checking system status...")
        status = command.GetSystemStatus()
        print(f"   Current status: {status.trackerProcessorStatus}")
        
        # 2. 初期化の確認
        if status.trackerProcessorStatus == ES_TPS_Initialized:
            print("✓ Initialization is Okay, Tracker is Ready.")
            return True
        else:
            print("⚠ Initialization is NOT Okay, Tracker is NOT Ready.")
            print("2. Attempting initialization...")
            command.Initialize()
            print("   Initialization command sent")
            return False
        
    except Exception as e:
        print(f"✗ Gradual initialization failed: {e}")
        return False

def set_measurement_mode():
    try:
        print("=== Set Measurement Mode (AT4xx) ===")
        
        # AT4xxでは静止測定モードのみ
        print("1. AT4xx supports only Stationary mode")
        print(f"   Mode: {ES_MM_Stationary} (Stationary)")
        
        # 測定モードを設定
        print("2. Setting measurement mode...")
        command.SetMeasurementMode(ES_MM_Stationary)
        print("   Measurement mode command sent")
        
        # 設定完了を待つ
        time.sleep(1)
        
        # 設定後の確認
        print("3. Verifying measurement mode...")
        response = command.GetMeasurementMode()
        print(f"new mode object: {response}")
        new_mode = response.measMode
        print(f"Current mode : {new_mode}")

        if new_mode == ES_MM_Stationary:
            print("✓ Stationary measurement mode set successfully")
            return True
        else:
            print("⚠ Measurement mode may not have been set correctly")
            return False        
            
    except Exception as e:
        print(f"✗ Failed to set measurement mode: {e}")
        return False
def get_Reflector():
    try:
        print("=== Get Reflector ===")
        print("1. Getting reflector...")
        response = command.GetReflector()
        print(f"new reflector object: {response}")
        reflector = response.iInternalReflectorId
        print(f"Current reflector: {reflector}")
    except Exception as e:
        print(f"Failed to get a reflector: {e}")
        return False
def get_Reflectors():
    """リフレクターの設定情報を取得（リフレクターを探すのではなく、設定データを読み取る）"""
    try:
        print("=== Get Reflectors (Settings) ===")
        print("1. Getting reflector settings...")
        response = command.GetReflectors()
        print(f"new reflectors object: {response}")
        
        # 単一のリフレクター情報を表示
        print(f"Total Reflectors: {response.iTotalReflectors}")
        print(f"Internal Reflector ID: {response.iInternalReflectorId}")
        print(f"Target Type: {response.targetType}")
        print(f"Surface Offset: {response.dSurfaceOffset}")
        
        # リフレクター名をデコード
        if response.cReflectorName:
            reflector_name = response.cReflectorName.decode('utf-16').rstrip('\x00')
            print(f"Reflector Name: {reflector_name}")
        else:
            print("Reflector Name: (empty)")
            
        print("✓ Reflector settings retrieved successfully")
        return True
        
    except Exception as e:
        print(f"Failed to get reflectors: {e}")
        return False

def find_reflector(distance=0.05):
    """実際にリフレクターを物理的に探す"""
    try:
        print("=== Find Reflector (Physical Search) ===")
        print(f"1. Searching for reflector at distance: {distance}m...")
        
        # リフレクターを物理的に検索
        response = command.FindReflector(distance)
        print(f"Find reflector response: {response}")
        
        print("✓ Reflector search completed")
        return True
        
    except Exception as e:
        print(f"Failed to find reflector: {e}")
        return False

def search_reflector_around():
    """リフレクターを周囲で検索"""
    try:
        print("=== Search Reflector Around ===")
        
        # 複数の距離で検索を試行
        distances = [5.0, 10.0, 20.0, 50.0]
        
        for distance in distances:
            print(f"Searching at distance: {distance}m...")
            try:
                response = command.FindReflector(distance)
                print(f"✓ Found reflector at distance: {distance}m")
                return True
            except Exception as e:
                print(f"✗ No reflector found at distance: {distance}m")
                continue
        
        print("✗ No reflector found in any distance range")
        return False
        
    except Exception as e:
        print(f"Failed to search reflector: {e}")
        return False
def set_reflector():
    try:
        print("=== Set Reflector ===")
        print("1. Setting reflector...")
        command.SetReflector(1)
        print("✓ Reflector set successfully")
    except Exception as e:
        print(f"Failed to set a reflector: {e}")
        return False
def go_bird_bath():
    try:
        command.GoBirdBath()
        print("✓ Go Bird Bath successful")
    except Exception as e:
        print(f"Failed to go bird bath: {e}")
        return False
def set_OrientationpParam():
    try:
        station_orientation = StationOrientationDataT()
        station_orientation.dVal1 = 0.0
        station_orientation.dVal2 = 0.0
        station_orientation.dVal3 = 0.0
        station_orientation.dRot1 = 0.0
        station_orientation.dRot2 = 0.0
        station_orientation.dRot3 = 0.0
        command.SetStationOrientationParams(station_orientation)
        print("✓ Set Params successful")
        response = command.GetStationOrientationParams()
        print(f"✓ Get Params successful {response.stationOrientation}")
    except Exception as e:
        print(f"Failed to set params: {e}")
        return False
def set_TransformationParam():
    try:
        transformation = TransformationDataT()
        transformation.dVal1 = 0.1
        transformation.dVal2 = 0.1
        transformation.dVal3 = 0.1
        transformation.dRot1 = 0.1
        transformation.dRot2 = 0.1
        transformation.dRot3 = 0.1
        transformation.dScale = 1.0
        command.SetTransformationParams(transformation)
        print("✓ Set Transformation Params successful")
        response = command.GetTransformationParams()
        print(f"✓ Get Transformation Params successful {response.transformationData}")
    except Exception as e:
        print(f"Failed to set params: {e}")
        return False
def set_CoordinateSystemType():
    try:
        coordinate_system = ES_CS_RHR
        command.SetCoordinateSystemType(coordinate_system)
        print("✓ Set Coordinate System Type successful")
        response = command.GetCoordinateSystemType()
        print(f"✓ Get Coordinate System Type successful {response.coordSysType}")
    except Exception as e:
        print(f"Failed to set coordinate system type: {e}")
        return False
def set_system_setting():
    try:
        system_setting = SystemSettingsDataT()
        system_setting.weatherMonitorStatus = ES_WMS_ReadOnly
        # パラメータ適用設定
        system_setting.bApplyStationOrientationParams = 1  # ステーション方向パラメータを適用
        system_setting.bApplyTransformationParams = 1      # 変換パラメータを適用
        
        # 動作設定
        system_setting.bKeepLastPosition = 1               # 最後の位置を保持
        system_setting.bSendUnsolicitedMessages = 1       # 未要求メッセージを送信
        system_setting.bSendReflectorPositionData = 0     # リフレクター位置データは送信しない
        
        # ハードウェア設定
        system_setting.bHasNivel = 1                       # レベルセンサーあり
        system_setting.bHasVideoCamera = 1                 # ビデオカメラあり
        
        command.SetSystemSettings(system_setting)
        print("✓ Set System Setting successful")
        response = command.GetSystemSettings()
        print(f"✓ Get System Setting successful {response.systemSettings}")
    except Exception as e:
        print(f"Failed to set system setting: {e}")
        return False
def find_reflector(distance=10.0):
    try:
        command.FindReflector(distance)
        print(f"✓ Find Reflector successful at distance {distance}m")
    except Exception as e:
        print(f"Failed to find reflector: {e}")
        return False
def check_measurement_prerequisites():
    """測定前の前提条件をチェック"""
    try:
        print("=== Checking Measurement Prerequisites ===")
        
        # 1. システムステータスを確認
        print("1. Checking system status...")
        try:
            status = command.GetSystemStatus()
            print(f"System Status: {status}")
        except Exception as e:
            print(f"Failed to get system status: {e}")
        
        # 2. トラッカーステータスを確認
        print("2. Checking tracker status...")
        try:
            tracker_status = command.GetTrackerStatus()
            print(f"Tracker Status: {tracker_status}")
        except Exception as e:
            print(f"Failed to get tracker status: {e}")
        
        # 3. リフレクターを探す
        print("3. Searching for reflector...")
        try:
            find_result = command.FindReflector(10.0)
            print(f"Find Reflector Result: {find_result}")
            print("✓ Reflector found")
        except Exception as e:
            print(f"Failed to find reflector: {e}")
            print("⚠️ No reflector found - measurement may fail")
        
        # 4. 測定モードを確認
        print("4. Checking measurement mode...")
        try:
            meas_mode = command.GetMeasurementMode()
            print(f"Measurement Mode: {meas_mode}")
        except Exception as e:
            print(f"Failed to get measurement mode: {e}")
        
        print("✓ Prerequisites check completed")
        return True
        
    except Exception as e:
        print(f"Failed to check prerequisites: {e}")
        return False

def go_to_position(x, y, z, use_adm=True):
    """指定した直交座標にレーザーを向ける"""
    try:
        print(f"=== Going to Position ({x}, {y}, {z}) ===")
        
        # 直交座標で指定した位置に移動
        result = command.GoPosition(use_adm, x, y, z)
        print(f"✓ Successfully moved to position ({x}, {y}, {z})")
        return result
        
    except Exception as e:
        print(f"Failed to go to position: {e}")
        return False

def go_to_position_hvd(distance, horizontal_angle, vertical_angle, use_adm=True):
    """指定した極座標にレーザーを向ける"""
    try:
        print(f"=== Going to Position HVD (Distance: {distance}, H: {horizontal_angle}°, V: {vertical_angle}°) ===")
        
        # 極座標で指定した位置に移動
        result = command.GoPositionHVD(use_adm, distance, horizontal_angle, vertical_angle)
        print(f"✓ Successfully moved to position HVD")
        return result
        
    except Exception as e:
        print(f"Failed to go to position HVD: {e}")
        return False

def go_to_origin():
    """原点(0, 0, 0)にレーザーを向ける"""
    try:
        print("=== Going to Origin (0, 0, 0) ===")
        return go_to_position(0.0, 0.0, 0.0)
    except Exception as e:
        print(f"Failed to go to origin: {e}")
        return False

def get_adm_info():
    """ADM（距離計）の情報を取得"""
    try:
        print("=== Getting ADM Information ===")
        
        # ADM情報を取得
        adm_info = command.GetADMInfo2()
        
        print(f"ADM Type: {adm_info.admType}")
        
        # ADM名をデコード
        if adm_info.cADMName:
            adm_name = adm_info.cADMName.decode('utf-16').rstrip('\x00')
            print(f"ADM Name: {adm_name}")
        else:
            print("ADM Name: (empty)")
            
        print(f"Serial Number: {adm_info.lSerialNumber}")
        print(f"Firmware Version: {adm_info.iFirmwareMajorVersionNumber}.{adm_info.iFirmwareMinorVersionNumber}")
        print(f"Max Distance: {adm_info.dMaxDistance:.2f} m")
        print(f"Min Distance: {adm_info.dMinDistance:.2f} m")
        print(f"Max Data Rate: {adm_info.iMaxDataRate} Hz")
        print(f"ADM Distance Accuracy: {adm_info.dAccuracyADMDistance:.6f} m")
        
        return {
            'admType': adm_info.admType,
            'admName': adm_name if adm_info.cADMName else '',
            'serialNumber': adm_info.lSerialNumber,
            'firmwareVersion': f"{adm_info.iFirmwareMajorVersionNumber}.{adm_info.iFirmwareMinorVersionNumber}",
            'maxDistance': adm_info.dMaxDistance,
            'minDistance': adm_info.dMinDistance,
            'maxDataRate': adm_info.iMaxDataRate,
            'accuracy': adm_info.dAccuracyADMDistance
        }
        
    except Exception as e:
        print(f"Failed to get ADM info: {e}")
        return None

def test_measurement():
    """測定を実行"""
    try:
        print("=== Starting Measurement ===")
        
        # 前提条件をチェック
        if not check_measurement_prerequisites():
            print("⚠️ Prerequisites check failed, but continuing...")
        
        # 測定を開始
        print("Starting measurement...")
        measurement = command.StartMeasurement()
        print("✓ Start Measurement successful")
        
        if measurement:
            print("✓ Measurement successful")
            result = {
                'measMode': measurement.measMode,
                'x': measurement.dVal1,
                'y': measurement.dVal2,
                'z': measurement.dVal3,
                'std1': measurement.dStd1,
                'std2': measurement.dStd2,
                'std3': measurement.dStd3,
                'stdTotal': measurement.dStdTotal,
            }
            return result
        else:
            print("✗ Measurement failed")
            return None
    except Exception as e:
        print(f"Failed to start measurement: {e}")
        return False




