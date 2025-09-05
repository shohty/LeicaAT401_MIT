import struct
# BasicCommandCTの処理を再現
from packet import BasicCommandCT, PacketHeaderT


def trace_packet_processing():
    """パケット処理の流れを追跡"""
    
    print("=== Packet Processing Flow ===")
    
    # 元の12バイトパケット
    original_packet = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C'
    print(f"1. Original packet: {original_packet}")
    print(f"   Length: {len(original_packet)} bytes")
    
    
    # ヘッダー部分を処理
    header = PacketHeaderT()
    remaining_packet = header.unpack(original_packet)
    print(f"\n2. After header.unpack(): {remaining_packet}")
    print(f"   Length: {len(remaining_packet)} bytes")
    
    # 残ったパケットからコマンドを抽出
    sizes = [4]
    formats = ['<I ']
    
    packet_elements = struct.Struct(formats[0]).unpack(remaining_packet[:sizes[0]])
    print(f"\n3. Command extraction: {packet_elements}")
    print(f"   Command value: {packet_elements[0]}")

if __name__ == "__main__":
    trace_packet_processing()

