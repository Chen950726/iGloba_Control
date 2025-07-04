#!/usr/bin/env python3
"""
iGloba Ed Robot Controller
基於 iGloba Ed 開放介面協定的 Python 控制程式
適用於 Ubuntu 系統
"""

import serial
import time
import struct
import threading
from typing import Optional, List, Tuple

class iGlobaEdController:
    """iGloba Ed 機器人控制器"""
    
    def __init__(self, port: str = '/dev/ttyUSB1', baudrate: int = 115200):
        """
        初始化機器人控制器
        
        Args:
            port: 串列埠位置 (例如: /dev/ttyUSB0, /dev/ttyACM0)
            baudrate: 傳輸速率 (預設: 115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.streaming = False
        self.stream_thread: Optional[threading.Thread] = None
        
    def connect(self) -> bool:
        """連接到機器人"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            print(f"已連接到 {self.port}")
            return True
        except Exception as e:
            print(f"連接失敗: {e}")
            return False
    
    def disconnect(self):
        """斷開連接"""
        if self.streaming:
            self.stop_stream()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("已斷開連接")
    
    def send_command(self, opcode: int, data: List[int] = None) -> bool:
        """
        發送命令到機器人
        
        Args:
            opcode: 操作碼
            data: 資料位元組列表
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("錯誤: 未連接到機器人")
            return False
        
        try:
            command = [opcode]
            if data:
                command.extend(data)
            
            self.serial_conn.write(bytes(command))
            self.serial_conn.flush()
            return True
        except Exception as e:
            print(f"發送命令失敗: {e}")
            return False
    
    # === 啟動命令 ===
    def start(self) -> bool:
        """啟動 OI (進入被動模式)"""
        print("啟動機器人...")
        return self.send_command(128)
    
    def reset(self) -> bool:
        """重置機器人 (進入關閉模式)"""
        print("重置機器人...")
        return self.send_command(7)
    
    def stop(self) -> bool:
        """停止 OI (進入關閉模式)"""
        print("停止機器人...")
        return self.send_command(173)
    
    # === 模式命令 ===
    def safe_mode(self) -> bool:
        """進入安全模式"""
        print("進入安全模式...")
        return self.send_command(131)
    
    def full_mode(self) -> bool:
        """進入完整模式"""
        print("進入完整模式...")
        return self.send_command(132)
    
    # === 清掃命令 ===
    def clean(self) -> bool:
        """開始一般清掃 (隨機模式)"""
        print("開始一般清掃...")
        return self.send_command(135)
    
    def max_clean(self) -> bool:
        """開始最大清掃 (隨機+不回充)"""
        print("開始最大清掃...")
        return self.send_command(136)
    
    def seek_dock(self) -> bool:
        """尋找充電座並回充"""
        print("尋找充電座...")
        return self.send_command(143)
    
    def power_off(self) -> bool:
        """關閉機器人電源"""
        print("關閉電源...")
        return self.send_command(133)
    
    # === 動作執行命令 ===
    def drive(self, velocity: int, radius: int) -> bool:
        """
        控制機器人行走
        
        Args:
            velocity: 速度 (-500 到 500 mm/s)
            radius: 半徑 (-2000 到 2000 mm)
                   特殊值: 32767/-1 = 直線, -1 = 順時針, 1 = 逆時針
        """
        # 限制範圍
        velocity = max(-500, min(500, velocity))
        radius = max(-2000, min(2000, radius))
        
        # 轉換為 2's complement 16-bit
        if velocity < 0:
            velocity = 65536 + velocity
        if radius < 0:
            radius = 65536 + radius
        
        vel_high = (velocity >> 8) & 0xFF
        vel_low = velocity & 0xFF
        rad_high = (radius >> 8) & 0xFF
        rad_low = radius & 0xFF
        
        print(f"行走: 速度={velocity-65536 if velocity > 32767 else velocity}mm/s, "
              f"半徑={radius-65536 if radius > 32767 else radius}mm")
        
        return self.send_command(137, [vel_high, vel_low, rad_high, rad_low])
    
    def drive_direct(self, left_velocity: int, right_velocity: int) -> bool:
        """
        直接控制左右輪速度
        
        Args:
            left_velocity: 左輪速度 (-500 到 500 mm/s)
            right_velocity: 右輪速度 (-500 到 500 mm/s)
        """
        # 限制範圍
        left_velocity = max(-500, min(500, left_velocity))
        right_velocity = max(-500, min(500, right_velocity))
        
        # 轉換為 2's complement 16-bit
        if left_velocity < 0:
            left_velocity = 65536 + left_velocity
        if right_velocity < 0:
            right_velocity = 65536 + right_velocity
        
        left_high = (left_velocity >> 8) & 0xFF
        left_low = left_velocity & 0xFF
        right_high = (right_velocity >> 8) & 0xFF
        right_low = right_velocity & 0xFF
        
        print(f"直接驅動: 左輪={left_velocity-65536 if left_velocity > 32767 else left_velocity}mm/s, "
              f"右輪={right_velocity-65536 if right_velocity > 32767 else right_velocity}mm/s")
        
        return self.send_command(145, [left_high, left_low, right_high, right_low])
    
    def drive_pwm(self, left_pwm: int, right_pwm: int) -> bool:
        """
        PWM 控制左右輪
        
        Args:
            left_pwm: 左輪 PWM (-255 到 255)
            right_pwm: 右輪 PWM (-255 到 255)
        """
        # 限制範圍
        left_pwm = max(-255, min(255, left_pwm))
        right_pwm = max(-255, min(255, right_pwm))
        
        # 轉換為 2's complement 16-bit
        if left_pwm < 0:
            left_pwm = 65536 + left_pwm
        if right_pwm < 0:
            right_pwm = 65536 + right_pwm
        
        left_high = (left_pwm >> 8) & 0xFF
        left_low = left_pwm & 0xFF
        right_high = (right_pwm >> 8) & 0xFF
        right_low = right_pwm & 0xFF
        
        print(f"PWM 驅動: 左輪={left_pwm-65536 if left_pwm > 32767 else left_pwm}, "
              f"右輪={right_pwm-65536 if right_pwm > 32767 else right_pwm}")
        
        return self.send_command(146, [left_high, left_low, right_high, right_low])
    
    def motors(self, side_brush: bool = False, vacuum_fan: bool = False) -> bool:
        """
        控制馬達 (側刷和吸塵風扇)
        
        Args:
            side_brush: 側刷開關
            vacuum_fan: 吸塵風扇開關
        """
        motor_byte = 0
        if side_brush:
            motor_byte |= 0x01  # bit 0
        if vacuum_fan:
            motor_byte |= 0x04  # bit 2
        
        print(f"馬達控制: 側刷={'開' if side_brush else '關'}, "
              f"吸塵風扇={'開' if vacuum_fan else '關'}")
        
        return self.send_command(138, [motor_byte])
    
    def leds(self, color: int = 0) -> bool:
        """
        控制 LED
        
        Args:
            color: LED 顏色 (0=關閉, 1=藍燈, 2=紅燈, 3=藍燈+紅燈)
        """
        color = max(0, min(3, color))
        color_names = ['關閉', '藍燈', '紅燈', '藍燈+紅燈']
        print(f"LED 控制: {color_names[color]}")
        
        return self.send_command(139, [color])
    
    # === 感測器命令 ===
    def read_sensor(self, packet_id: int) -> Optional[bytes]:
        """
        讀取感測器資料
        
        Args:
            packet_id: 資料包編號
        """
        if self.send_command(142, [packet_id]):
            time.sleep(0.1)  # 等待回應
            if self.serial_conn.in_waiting > 0:
                return self.serial_conn.read(self.serial_conn.in_waiting)
        return None
    
    def query_sensors(self, packet_ids: List[int]) -> Optional[bytes]:
        """
        查詢多個感測器資料
        
        Args:
            packet_ids: 資料包編號列表
        """
        command_data = [len(packet_ids)] + packet_ids
        if self.send_command(149, command_data):
            time.sleep(0.1)  # 等待回應
            if self.serial_conn.in_waiting > 0:
                return self.serial_conn.read(self.serial_conn.in_waiting)
        return None
    
    def start_stream(self, packet_ids: List[int]):
        """
        開始資料流
        
        Args:
            packet_ids: 要串流的資料包編號列表
        """
        command_data = [len(packet_ids)] + packet_ids
        if self.send_command(148, command_data):
            self.streaming = True
            self.stream_thread = threading.Thread(target=self._stream_reader)
            self.stream_thread.daemon = True
            self.stream_thread.start()
            print(f"開始資料流: {packet_ids}")
    
    def pause_stream(self, pause: bool = True):
        """
        暫停/恢復資料流
        
        Args:
            pause: True=暫停, False=恢復
        """
        state = 0 if pause else 1
        self.send_command(150, [state])
        print(f"資料流: {'暫停' if pause else '恢復'}")
    
    def stop_stream(self):
        """停止資料流"""
        self.streaming = False
        if self.stream_thread:
            self.stream_thread.join(timeout=1)
        print("停止資料流")
    
    def _stream_reader(self):
        """資料流讀取執行緒"""
        while self.streaming:
            if self.serial_conn.in_waiting > 0:
                data = self.serial_conn.read(self.serial_conn.in_waiting)
                self._parse_stream_data(data)
            time.sleep(0.015)  # 15ms 間隔
    
    def _parse_stream_data(self, data: bytes):
        """解析資料流資料"""
        if len(data) >= 3 and data[0] == 19:  # 資料流標頭
            print(f"接收資料流: {data.hex()}")
            self.parse_sensor_data(data[2:])  # 跳過標頭解析資料
    
    # === 便利方法 ===
    def move_forward(self, speed: int = 200, duration: float = 1.0):
        """向前移動"""
        print(f"向前移動 {duration} 秒, 速度 {speed}mm/s")
        self.drive(speed, 32767)  # 直線移動
        time.sleep(duration)
        self.drive(0, 0)  # 停止
        print(f"已經停止")

    
    def move_backward(self, speed: int = 200, duration: float = 1.0):
        """向後移動"""
        print(f"向後移動 {duration} 秒, 速度 {speed}mm/s")
        self.drive(-speed, 32767)  # 直線移動
        time.sleep(duration)
        self.drive(0, 0)  # 停止
        print(f"已經停止")
    
    def turn_left(self, duration: float = 1.0):
        """左轉"""
        print(f"左轉 {duration} 秒")
        self.drive(200, 1)  # 逆時針旋轉
        time.sleep(duration)
        self.drive(0, 0)  # 停止
    
    def turn_right(self, duration: float = 1.0):
        """右轉"""
        print(f"右轉 {duration} 秒")
        self.drive(200, -1)  # 順時針旋轉
        time.sleep(duration)
        self.drive(0, 0)  # 停止
    
    def stop_movement(self):
        """停止移動"""
        print("停止移動")
        self.drive(0, 0)
    
    # === 感測器資料解析方法 ===
    def parse_sensor_data(self, data: bytes, packet_id: int = None):
        """
        解析感測器資料
        
        Args:
            data: 原始感測器資料
            packet_id: 指定的封包ID (如果已知)
        """
        if not data:
            return None
        
        # 如果沒有指定封包ID，嘗試從資料中識別
        if packet_id is None:
            if len(data) >= 1:
                packet_id = data[0]
                data = data[1:]  # 跳過封包ID
        
        result = {}
        
        try:
            if packet_id == 7:  # IR Bumps and Drops
                result = self._parse_ir_bumps_drops(data)
            elif packet_id == 8:  # Guide Sensors Signal Detect
                result = self._parse_guide_sensors_flag(data)
            elif packet_id == 9:  # IR Bumps Signal Level
                result = self._parse_ir_signal_level(data)
            elif packet_id == 10:  # Guide Sensors Signal Level
                result = self._parse_guide_signal_level(data)
            elif packet_id == 11:  # Motors Overcurrents
                result = self._parse_motor_overcurrents(data)
            elif packet_id == 12:  # Charging Source and State
                result = self._parse_charging_state(data)
            elif packet_id == 13:  # Battery Voltage
                result = self._parse_battery_voltage(data)
            elif packet_id == 15:  # Requested Velocity
                result = self._parse_requested_velocity(data)
            elif packet_id == 16:  # Requested Radius
                result = self._parse_requested_radius(data)
            elif packet_id == 17:  # Requested Left/Right Velocity
                result = self._parse_requested_lr_velocity(data)
            elif packet_id == 18:  # Left/Right Encoder Counts
                result = self._parse_encoder_counts(data)
            elif packet_id == 19:  # Operate Mode
                result = self._parse_operate_mode(data)
            elif packet_id == 20:  # Motors Current
                result = self._parse_motors_current(data)
            else:
                result = {"packet_id": packet_id, "raw_data": data.hex()}
                
        except Exception as e:
            result = {"error": f"解析錯誤: {e}", "packet_id": packet_id, "raw_data": data.hex()}
        
        return result
    
    def _parse_ir_bumps_drops(self, data: bytes) -> dict:
        """解析 IR 防碰撞和落下感測器 (封包 7)"""
        if len(data) < 2:
            return {"error": "資料長度不足"}
        
        # 16-bit 資料
        value = (data[0] << 8) | data[1]
        
        # IR 防碰撞感測器 (bit 0-6)
        ir_bumps = []
        for i in range(7):
            ir_bumps.append(bool(value & (1 << i)))
        
        # 落下感測器 (bit 9-11)
        drop_sensors = []
        for i in range(3):
            drop_sensors.append(bool(value & (1 << (9 + i))))
        
        return {
            "packet_id": 7,
            "ir_bumps": {
                "sensor_1": ir_bumps[0],
                "sensor_2": ir_bumps[1],
                "sensor_3": ir_bumps[2],
                "sensor_4": ir_bumps[3],
                "sensor_5": ir_bumps[4],
                "sensor_6": ir_bumps[5],
                "sensor_7": ir_bumps[6]
            },
            "drop_sensors": {
                "sensor_1": drop_sensors[0],
                "sensor_2": drop_sensors[1],
                "sensor_3": drop_sensors[2]
            },
            "raw_value": value
        }
    
    def _parse_guide_sensors_flag(self, data: bytes) -> dict:
        """解析 Guide 感測器旗標和類型 (封包 8)"""
        if len(data) < 2:
            return {"error": "資料長度不足"}
        
        value = (data[0] << 8) | data[1]
        
        # 解析各個 Guide 感測器
        sensors = {}
        for i in range(4):
            sensor_num = i + 1
            # 訊號類型 (每個感測器 2 bits)
            signal_type = (value >> (i * 2)) & 0x03
            signal_types = ["無訊號", "充電座中央訊號(2K)", "充電座右側訊號(10K)", "充電座左側訊號(5K)"]
            
            # 檢測旗標
            flag_detected = bool(value & (1 << (12 + i)))
            
            sensors[f"guide_sensor_{sensor_num}"] = {
                "signal_type": signal_types[signal_type],
                "signal_detected": flag_detected
            }
        
        return {
            "packet_id": 8,
            "guide_sensors": sensors,
            "raw_value": value
        }
    
    def _parse_ir_signal_level(self, data: bytes) -> dict:
        """解析 IR 防碰撞感測器訊號值 (封包 9)"""
        if len(data) < 14:
            return {"error": "資料長度不足"}
        
        sensors = {}
        for i in range(7):
            offset = i * 2
            value = (data[offset] << 8) | data[offset + 1]
            sensors[f"ir_sensor_{i+1}"] = value
        
        return {
            "packet_id": 9,
            "ir_signal_levels": sensors,
            "max_value": 4095
        }
    
    def _parse_guide_signal_level(self, data: bytes) -> dict:
        """解析 Guide 感測器訊號值 (封包 10)"""
        if len(data) < 8:
            return {"error": "資料長度不足"}
        
        sensors = {}
        for i in range(4):
            offset = i * 2
            value = (data[offset] << 8) | data[offset + 1]
            sensors[f"guide_sensor_{i+1}"] = value
        
        return {
            "packet_id": 10,
            "guide_signal_levels": sensors,
            "max_value": 4095
        }
    
    def _parse_motor_overcurrents(self, data: bytes) -> dict:
        """解析馬達過電流狀態 (封包 11)"""
        if len(data) < 1:
            return {"error": "資料長度不足"}
        
        value = data[0]
        
        return {
            "packet_id": 11,
            "motor_overcurrents": {
                "left_wheel": bool(value & 0x01),
                "right_wheel": bool(value & 0x02),
                "side_brush": bool(value & 0x04),
                "vacuum_motor": bool(value & 0x08)
            },
            "raw_value": value
        }
    
    def _parse_charging_state(self, data: bytes) -> dict:
        """解析充電來源和狀態 (封包 12)"""
        if len(data) < 1:
            return {"error": "資料長度不足"}
        
        value = data[0]
        state = value & 0x03
        source_dc = bool(value & 0x04)
        source_dock = bool(value & 0x08)
        
        states = ["未充電", "已充飽", "充電中", "充電錯誤"]
        
        return {
            "packet_id": 12,
            "charging_state": states[state],
            "charging_sources": {
                "dc_adapter": source_dc,
                "charging_dock": source_dock
            },
            "raw_value": value
        }
    
    def _parse_battery_voltage(self, data: bytes) -> dict:
        """解析電池電壓 (封包 13)"""
        if len(data) < 2:
            return {"error": "資料長度不足"}
        
        voltage = (data[0] << 8) | data[1]
        
        return {
            "packet_id": 13,
            "battery_voltage_mv": voltage,
            "battery_voltage_v": voltage / 1000.0
        }
    
    def _parse_requested_velocity(self, data: bytes) -> dict:
        """解析請求速度 (封包 15)"""
        if len(data) < 2:
            return {"error": "資料長度不足"}
        
        velocity = (data[0] << 8) | data[1]
        # 轉換 2's complement
        if velocity > 32767:
            velocity = velocity - 65536
        
        return {
            "packet_id": 15,
            "requested_velocity_mms": velocity
        }
    
    def _parse_requested_radius(self, data: bytes) -> dict:
        """解析請求半徑 (封包 16)"""
        if len(data) < 2:
            return {"error": "資料長度不足"}
        
        radius = (data[0] << 8) | data[1]
        # 轉換 2's complement
        if radius > 32767:
            radius = radius - 65536
        
        # 特殊值處理
        if radius == 32767 or radius == -32768:
            radius_desc = "直線"
        elif radius == -1:
            radius_desc = "順時針旋轉"
        elif radius == 1:
            radius_desc = "逆時針旋轉"
        else:
            radius_desc = f"{radius}mm"
        
        return {
            "packet_id": 16,
            "requested_radius_mm": radius,
            "radius_description": radius_desc
        }
    
    def _parse_requested_lr_velocity(self, data: bytes) -> dict:
        """解析左右輪請求速度 (封包 17)"""
        if len(data) < 4:
            return {"error": "資料長度不足"}
        
        left_vel = (data[0] << 8) | data[1]
        right_vel = (data[2] << 8) | data[3]
        
        # 轉換 2's complement
        if left_vel > 32767:
            left_vel = left_vel - 65536
        if right_vel > 32767:
            right_vel = right_vel - 65536
        
        return {
            "packet_id": 17,
            "left_wheel_velocity_mms": left_vel,
            "right_wheel_velocity_mms": right_vel
        }
    
    def _parse_encoder_counts(self, data: bytes) -> dict:
        """解析編碼器計數 (封包 18)"""
        if len(data) < 4:
            return {"error": "資料長度不足"}
        
        left_count = (data[0] << 8) | data[1]
        right_count = (data[2] << 8) | data[3]
        
        return {
            "packet_id": 18,
            "left_encoder_count": left_count,
            "right_encoder_count": right_count
        }
    
    def _parse_operate_mode(self, data: bytes) -> dict:
        """解析操作模式 (封包 19)"""
        if len(data) < 1:
            return {"error": "資料長度不足"}
        
        mode = data[0] & 0x03
        modes = ["關閉(Off)", "被動(Passive)", "安全(Safe)", "完整(Full)"]
        
        return {
            "packet_id": 19,
            "operate_mode": modes[mode],
            "mode_value": mode
        }
    
    def _parse_motors_current(self, data: bytes) -> dict:
        """解析馬達電流 (封包 20)"""
        if len(data) < 8:
            return {"error": "資料長度不足"}
        
        left_current = (data[0] << 8) | data[1]
        right_current = (data[2] << 8) | data[3]
        side_brush_current = (data[4] << 8) | data[5]
        main_brush_current = (data[6] << 8) | data[7]
        
        return {
            "packet_id": 20,
            "motor_currents": {
                "left_wheel_ma": left_current,
                "right_wheel_ma": right_current,
                "side_brush_ma": side_brush_current,
                "main_brush_ma": main_brush_current
            }
        }
    
    def read_and_parse_sensor(self, packet_id: int) -> dict:
        """
        讀取並解析感測器資料
        
        Args:
            packet_id: 感測器封包ID
            
        Returns:
            解析後的感測器資料字典
        """
        raw_data = self.read_sensor(packet_id)
        if raw_data:
            return self.parse_sensor_data(raw_data, packet_id)
        return None
    
    def get_all_sensors(self) -> dict:
        """讀取所有主要感測器資料"""
        sensors = {}
        
        # 主要感測器封包
        important_packets = [7, 11, 12, 13, 19]
        
        for packet_id in important_packets:
            try:
                data = self.read_and_parse_sensor(packet_id)
                if data:
                    sensors[f"packet_{packet_id}"] = data
                time.sleep(0.05)  # 避免過快請求
            except Exception as e:
                sensors[f"packet_{packet_id}"] = {"error": str(e)}
        
        return sensors
    
    def print_sensor_status(self):
        """列印感測器狀態摘要"""
        print("=" * 50)
        print("機器人感測器狀態")
        print("=" * 50)
        
        # 操作模式
        mode_data = self.read_and_parse_sensor(19)
        if mode_data and 'operate_mode' in mode_data:
            print(f"操作模式: {mode_data['operate_mode']}")
        
        # 電池電壓
        battery_data = self.read_and_parse_sensor(13)
        if battery_data and 'battery_voltage_v' in battery_data:
            voltage = battery_data['battery_voltage_v']
            print(f"電池電壓: {voltage:.2f}V ({battery_data['battery_voltage_mv']}mV)")
        
        # 充電狀態
        charging_data = self.read_and_parse_sensor(12)
        if charging_data and 'charging_state' in charging_data:
            print(f"充電狀態: {charging_data['charging_state']}")
            sources = charging_data['charging_sources']
            if sources['dc_adapter'] or sources['charging_dock']:
                print(f"充電來源: DC={'是' if sources['dc_adapter'] else '否'}, "
                      f"充電座={'是' if sources['charging_dock'] else '否'}")
        
        # IR 防碰撞感測器
        ir_data = self.read_and_parse_sensor(7)
        if ir_data and 'ir_bumps' in ir_data:
            bumps = ir_data['ir_bumps']
            active_bumps = [k for k, v in bumps.items() if v]
            if active_bumps:
                print(f"IR 防碰撞觸發: {', '.join(active_bumps)}")
            else:
                print("IR 防碰撞: 正常")
        
        # 落下感測器
        if ir_data and 'drop_sensors' in ir_data:
            drops = ir_data['drop_sensors']
            active_drops = [k for k, v in drops.items() if v]
            if active_drops:
                print(f"落下感測器觸發: {', '.join(active_drops)}")
            else:
                print("落下感測器: 正常")
        
        # 馬達過電流
        motor_data = self.read_and_parse_sensor(11)
        if motor_data and 'motor_overcurrents' in motor_data:
            overcurrents = motor_data['motor_overcurrents']
            active_oc = [k for k, v in overcurrents.items() if v]
            if active_oc:
                print(f"馬達過電流: {', '.join(active_oc)}")
            else:
                print("馬達電流: 正常")
        
        print("=" * 50)

def main():
    """主程式 - 示範用法"""
    print("iGloba Ed 機器人控制器")
    print("=" * 30)
    
    # 建立控制器實例
    robot = iGlobaEdController('/dev/ttyUSB1')  # 根據實際情況修改埠號
    
    try:
        if not robot.connect():
            return

        robot.start()
        time.sleep(0.5)


        # 進入完整模式 (不受落地/充電限制)
        if not robot.full_mode():
            print("進入完整模式失敗")
            return

        # 確認目前模式
        mode_data = robot.read_and_parse_sensor(19)
        if mode_data:
            print(f"[DEBUG] 目前模式: {mode_data.get('operate_mode', '未知')}")
        else:
            print("[DEBUG] 無法取得操作模式（封包 19），請檢查感測器回應")

        # 執行動作
        robot.move_forward(speed=200, duration=1.5)
        # 印出感測狀態
        robot.print_sensor_status()

        print("\n示範完成!")
    
    except KeyboardInterrupt:
        print("\n程式被中斷")
    except Exception as e:
        print(f"錯誤: {e}")
    finally:
        robot.disconnect()

if __name__ == "__main__":
    main()
