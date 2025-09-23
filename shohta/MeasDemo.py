import sys
import os
import ROOT
import logging
import time
import datetime
import threading
import csv
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
##Excute functions below at the top directory of this API
##Before connection,  check that any other PCs are not connected to the tracker(192.168.0.2:700)
##connection->sync_command (after sync_command, do check_connection, for just in case)
##If it doesn't work, try disconnect_from_tracker and then do the same process again
##If it still doesn't work, reboot the tracker and reconnect the LAN cable to your PC 
def first_setup():
    set_measurement_mode()
    set_weathermonitor()
    set_OrientationpParam()
    set_TransformationParam()
    setADM()
    set_CoordinateSystemType(7)
    set_system_setting()
def setADM():
    try:
        print("=== Setting ADM ===")
        stationary_params = StationaryModeDataT()
        stationary_params.lMeasTime = 2000  # Measuring Time (ms)
        stationary_params.bUseADM = 0      # don't use ADM because EMMA doesen't use it (no effect; still set to 1)
        # setting Parameters
        command.SetStationaryModeParams(stationary_params)
        newADM = command.GetStationaryModeParams().stationaryModeData.bUseADM
        if newADM == 0:
            print("✓ ADM set successfully")
        else:
            print("✗ ADM set failed")
            return False
        #print(f"✓ ADM set successfully {newADM}")
        return True
    except Exception as e:
        print(f"Failed to set ADM: {e}")
        return False


def set_weathermonitor():
    try:
        response = command.GetSystemSettings()
        settings = response.systemSettings
        WeatherMonitorStatus = settings.weatherMonitorStatus
        if WeatherMonitorStatus == ES_WMS_NotConnected or WeatherMonitorStatus == ES_WMS_ReadOnly:
            print("✓ Weather monitor is not Okay")
            settings.weatherMonitorStatus = ES_WMS_ReadAndCalculateRefractions
            command.SetSystemSettings(settings)
            new_weathermonitorstatus = command.GetSystemSettings().systemSettings.weatherMonitorStatus
            print(f"✓ Weather monitor set to ReadAndCalculateRefractions {new_weathermonitorstatus}")
            return True
        elif WeatherMonitorStatus == ES_WMS_ReadAndCalculateRefractions:
            print("✓ Weather monitor is already set to ReadAndCalculateRefractions")
            return True
        else:
            print("✗ Weather monitor is not Okay")
            return False
    except Exception as e:
        print(f"Failed to set weather monitor: {e}")
        return False
def check_connection():
    try:
        print("=== Checking Connection ===")
        print("1. Checking connection...")
        response = command.GetTrackerInfo()#check connection with a simple command
        print(f"new status object: {response}")
        trackername = response.cTrackerName
        print(f"Tracker Name: {trackername.decode('utf-16').rstrip('\x00')}")
        print("✓ Connection check successful")
        return True
    except Exception as e:
        print(f"Failed to check connection: {e}")
        return False
def disconnect_from_tracker():
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
    units.lenUnitType = ES_LU_Millimeter     
    units.angUnitType = ES_AU_Radian         
    units.tempUnitType = ES_TU_Fahrenheit  #set same as AT Controler otherwise it'll be out of range  
    units.pressUnitType = ES_PU_InHg       #set same as AT Controler otherwise it'll be out of range  
    units.humUnitType = ES_HU_RH              
    command.SetUnits(units)
    print(f'Units set successfully')
def get_units():
    units = command.GetUnits()
    print(f'Length Unit Type: {units.unitsSettings.lenUnitType}')     
    print(f'Angle Unit Type: {units.unitsSettings.angUnitType}')
    print(f'Temperature Unit Type: {units.unitsSettings.tempUnitType}')
    print(f'Pressure Unit Type: {units.unitsSettings.pressUnitType}')
    print(f'Humidity Unit Type: {units.unitsSettings.humUnitType}')
def get_environment_info():
    try:
        #get the environment parameters
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
    try:
        print("=== Setting Environment Parameters ===")
        
        # 1. check the system settings
        settings = check_system_settings()
        if settings and settings.weatherMonitorStatus != ES_WMS_NotConnected:
            print("⚠️ Weather monitor is connected. Manual environment setting may conflict.")
            print("Consider setting weather monitor to 'Not Connected' first.")
        
        # 2. get the current environment parameters
        current_env_response = command.GetEnvironmentParams()
        current_env = current_env_response.environmentData
        print(f"Current - Temperature: {current_env.dTemperature:.2f} °F")
        print(f"Current - Pressure: {current_env.dPressure:.2f} inHg ")
        print(f"Current - Humidity: {current_env.dHumidity:.2f} %")
        command.SetEnvironmentParams(current_env)
        print("✓ Environment params set successfully")
        return True
        '''
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
        '''
        
    except Exception as e:
        print(f"Failed to set environment params: {e}")
        return False

def disable_weather_monitor():
    try:
        print("=== Disabling Weather Monitor ===")
        
        # システム設定を取得
        settings_response = command.GetSystemSettings()
        settings = settings_response.systemSettings
        print(f"")
        
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
    try:
        print("=== Gradual Initialization ===")
        
        # 1. check the system status
        print("1. Checking system status...")
        status = command.GetSystemStatus()
        print(f"   Current status: {status.trackerProcessorStatus}")
        
        # 2. check the initialization status
        if status.trackerProcessorStatus == ES_TPS_Initialized:
            print("✓ Initialization is Okay, Tracker is Ready.")
            return True
        else:
            print("⚠ Initialization is NOT Okay, Tracker is NOT Ready.")
            print("2. Attempting initialization...")
            command.Initialize()
            print("   Initialization command sent")
            return True
        
    except Exception as e:
        print(f"✗ Gradual initialization failed: {e}")
        return False

def set_measurement_mode():
    try:
        print("=== Set Measurement Mode (AT4xx) ===")
        
        # AT4xx supports only Stationary mode
        print("1. AT4xx supports only Stationary mode")
        print(f"   Mode: {ES_MM_Stationary} (Stationary)")
        
        # set the measurement mode
        print("2. Setting measurement mode...")
        command.SetMeasurementMode(ES_MM_Stationary)
        print("   Measurement mode command sent")
        
        # wait for the setting to be completed
        time.sleep(1)
        
        # check the measurement mode after setting
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
def set_CoordinateSystemType(coordsystype):
    try:
        #coordinate_system = ES_CS_RHR
        #coordinate_system = ES_CS_SCC#EMMA deploys this system
        command.SetCoordinateSystemType(coordsystype)
        print("✓ Set Coordinate System Type successful")
        response = command.GetCoordinateSystemType()
        print(f"✓ Get Coordinate System Type successful {response.coordSysType}")
    except Exception as e:
        print(f"Failed to set coordinate system type: {e}")
        return False
def set_system_setting():
    try:
        system_setting = SystemSettingsDataT()
        system_setting.weatherMonitorStatus = ES_WMS_ReadAndCalculateRefractions
        # パラメータ適用設定
        system_setting.bApplyStationOrientationParams = 1  # Apply Station Orientation Params
        system_setting.bApplyTransformationParams = 0    # NOT Apply Transformation Params
        
        # 動作設定
        system_setting.bKeepLastPosition = 1               # keep last position
        system_setting.bSendUnsolicitedMessages = 1       # send unsolicited messages
        system_setting.bSendReflectorPositionData = 1     # send reflector position data
        
        # ハードウェア設定
        system_setting.bTryMeasurementMode = 1            #set to try measurement mode
        system_setting.bHasNivel = 1                   # Level sensor is mounted
        system_setting.bHasVideoCamera = 1                 # The video camera is mounted
        
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
        
        # 1. check the system status
        print("1. Checking system status...")
        try:
            status = command.GetSystemStatus()
            print(f"System Status: {status}")
        except Exception as e:
            print(f"Failed to get system status: {e}")
        
        # 2. check the tracker status
        print("2. Checking tracker status...")
        try:
            tracker_status = command.GetTrackerStatus()
            print(f"Tracker Status: {tracker_status}")
        except Exception as e:
            print(f"Failed to get tracker status: {e}")
        
        # 3. search for a reflector
        print("3. Searching for reflector...")
        try:
            find_result = command.FindReflector(10.0)
            print(f"Find Reflector Result: {find_result}")
            print("✓ Reflector found")
        except Exception as e:
            print(f"Failed to find reflector: {e}")
            print("⚠️ No reflector found - measurement may fail")
        
        # 4. check the measurement mode
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

def go_to_position(x, y, z, use_adm=False):
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

def go_to_position_hvd(distance, horizontal_angle, vertical_angle, use_adm=False):
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

def measure():
    """Single Measurement"""
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
            result = {
                'measMode': measurement.measMode,
                'val1': measurement.dVal1,
                'val2': measurement.dVal2,
                'val3': measurement.dVal3,
                'std1': measurement.dStd1,
                'std2': measurement.dStd2,
                'std3': measurement.dStd3,
                'stdTotal': measurement.dStdTotal,
            }
            os.system('afplay Sounds/Blow.aiff')
            print(f"Measurement Done !!")
            return result
        else:
            print("✗ Measurement failed")
            os.system('afplay Sounds/Sosumi.aiff')
            return None
    except Exception as e:
        print(f"Failed to start measurement: {e}")
        return False

def initialize_roottree():
    """ initialize ROOT tree """
    tree = ROOT.TTree("LTtree","Leica Laser Tracker measurement")

    #Define branches
    measMode = ROOT.std.vector('int')()
    #timestamp_str = ROOT.std.vector('string')()  # "2023-12-21 12:34:56"
    date_str = ROOT.std.vector('string')()       # "2023-12-21"
    time_str = ROOT.std.vector('string')()       # "12:34:56"
    x = ROOT.std.vector('double')()
    y = ROOT.std.vector('double')()
    z = ROOT.std.vector('double')()
    std1 = ROOT.std.vector('double')()
    std2 = ROOT.std.vector('double')()
    std3 = ROOT.std.vector('double')()
    stdTotal = ROOT.std.vector('double')()

    tree.Branch("measMode", measMode)
    #tree.Branch("timestamp_str", timestamp_str)
    tree.Branch("date_str", date_str)
    tree.Branch("time_str", time_str)
    tree.Branch("x", x)
    tree.Branch("y", y)
    tree.Branch("z", z)
    tree.Branch("std1", std1)
    tree.Branch("std2", std2)
    tree.Branch("std3", std3)
    tree.Branch("stdTotal", stdTotal)


    return tree,(measMode, date_str, time_str, x,y, z, std1, std2, std3, stdTotal)

def fill_tree(tree, branch_vars, result):
    """ fill ROOT tree """
    measMode, date_str, time_str,x, y, z, std1, std2, std3, stdTotal = branch_vars
    #clear every time
    measMode.clear()
    #timestamp_str.clear()
    date_str.clear()
    time_str.clear()
    x.clear()
    y.clear()
    z.clear()
    std1.clear()
    std2.clear()
    std3.clear()
    stdTotal.clear()

    #fill new data
    measMode.push_back(result['measMode'])
    now = datetime.datetime.now()
    #timestamp_str.push_back(now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]) # fill time  
    date_str.push_back(now.strftime("%Y-%m-%d"))
    time_str.push_back(now.strftime("%H:%M:%S.%f")[:-3])
    x.push_back(result['x'])
    y.push_back(result['y'])
    z.push_back(result['z'])
    std1.push_back(result['std1'])
    std2.push_back(result['std2'])
    std3.push_back(result['std3'])
    stdTotal.push_back(result['stdTotal'])
    tree.Fill()

def point_measure(pointsname, repeat_num):
    print(f"=== Starting {pointsname} Measurements ===")
    #repeat_num = 1 #temporarily set to 5 times measure for each point
    # 日付ベースのファイル名
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    csvFileName = f"shohta/log/measurements_{today}.csv"
    get_coord = command.GetCoordinateSystemType()
    coordsystype = get_coord.coordSysType

    # CSVファイルの準備
    csv_data = []
    # should update to set axes name actively
    csv_headers = ['coordsystype', 'point_name', 'measurement_id', 'measMode', 'date', 'time', 'val1', 'val2', 'val3', 'std1', 'std2', 'std3', 'stdTotal']

    successful_measurements = 0
    failed_measurements = 0
    for i in range(repeat_num):
        print(f"=== Measurement {i+1} / {repeat_num} ===")
        try:
            result = measure() # single measurement
            if result:
                
                # CSVデータに追加
                now = datetime.datetime.now()
                csv_row = [
                    coordsystype, # coordinate system type (it's defined by numbers, see Programmer's manual)
                    pointsname,  # point_name
                    i+1,  # measurement_id
                    result['measMode'],
                    now.strftime("%Y-%m-%d"),
                    now.strftime("%H:%M:%S.%f")[:-3],
                    result['val1'],
                    result['val2'],
                    result['val3'],
                    result['std1'],
                    result['std2'],
                    result['std3'],
                    result['stdTotal']
                ]
                csv_data.append(csv_row)
                
                successful_measurements += 1
                print(f"✓ Measurement {i+1} successful")
            else:
                failed_measurements += 1
                print(f"✗ Measurement {i+1}/{repeat_num} failed")
        except Exception as e:
            failed_measurements += 1
            print(f"✗ Measurement {i+1}/{repeat_num} error: {e}")

        # mesurement interval time (optional)
        time.sleep(1.0)
    print(f"=== {repeat_num} Measurements Done ===")
    print(f"✓ {successful_measurements} measurements successful")
    print(f"✗ {failed_measurements} measurements failed")
    
    # record the data to csv file
    print(f"=== Saving to {csvFileName} ===")
    file_exists = os.path.exists(csvFileName)
    with open(csvFileName, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # if the csv file doesn't exist, make the file and insert the header first.
        if not file_exists:
            writer.writerow(csv_headers)
        writer.writerows(csv_data)
    print(f"✓ Successfully saved {len(csv_data)} measurements to {csvFileName}")
    return True
    
def soundtest():
    os.system('afplay Sounds/Blow.aiff')
    time.sleep(1.0)
    os.system('afplay Sounds/Sosumi.aiff')
    print("✓ Sound test successful")
    return True
