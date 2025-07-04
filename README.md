

# iGloba\_Control

**iGloba\_Control** 是一個基於 Python 串列埠通訊的機器人控制工具，專為控制 **iGloba Ed/Z07 系列掃地機器人** 而設計。透過本工具，你可以透過 UART 指令操作掃地機器人的啟動、移動、清掃、感測器資料讀取等功能。

> 📦 專為 Ubuntu/Linux 系統開發，支援 iGloba Ed 開放控制協定。



## 📌 特色 Features

* ✅ 支援 UART 連線 (115200 baud)
* 🚀 支援 robot 移動指令 (drive、turn、PWM、直接控制)
* 🧹 提供清掃控制（普通、最大、尋找充電座）
* 🔋 感測器資料即時讀取與解析（電壓、碰撞、掉落、充電狀態等）
* 🔄 支援資料串流模式
* 💡 支援 LED 與馬達控制（風扇/側刷）



## 🔧 環境需求 Requirements

* Python 3.6+
* Ubuntu 20.04 或以上版本
* 安裝 `pyserial` 套件：

```bash
pip install pyserial
```



## 🚀 安裝 Installation

```bash
git clone https://github.com/yourname/iGloba_Control.git
cd iGloba_Control
python3 igloba_ed_controller.py
```

> 請依照你實際的 port 修改 `controller = iGlobaEdController('/dev/ttyUSB0')`。



## 🕹️ 基本操作 Usage

### 連接與啟動

```python
controller = iGlobaEdController('/dev/ttyUSB0')
controller.connect()
controller.start()
controller.full_mode()
```

### 移動控制

```python
controller.move_forward(speed=200, duration=2)
controller.turn_left(duration=1)
controller.stop_movement()
```

### 清掃控制

```python
controller.clean()
controller.max_clean()
controller.seek_dock()
```

### 感測器讀取

```python
sensor_data = controller.get_all_sensors()
print(sensor_data)
```



## 📄 支援指令摘要

| 功能      | 指令碼                                                       |
| ------- | --------------------------------------------------------- |
| 啟動 OI   | `controller.start()`                                      |
| 進入完整模式  | `controller.full_mode()`                                  |
| 前進 / 後退 | `controller.move_forward()`, `controller.move_backward()` |
| 左右轉     | `controller.turn_left()`, `controller.turn_right()`       |
| 停止      | `controller.stop_movement()`                              |
| 清掃 / 回充 | `controller.clean()`, `controller.seek_dock()`            |
| 讀取感測器   | `controller.read_and_parse_sensor(packet_id)`             |
| LED 控制  | `controller.leds(color=1)`                                |
| 馬達開關    | `controller.motors(side_brush=True, vacuum_fan=True)`     |



## 📦 支援的感測器封包 (常見 ID)

| 封包 ID | 描述          |
| ----- | ----------- |
| 7     | IR 碰撞與落下感測器 |
| 11    | 馬達過電流狀態     |
| 12    | 充電狀態        |
| 13    | 電池電壓        |
| 19    | 操作模式        |

---

## 👨‍💻 示範程式 Demo

`igloba_ed_controller.py` 內含主程式 `main()`，展示從連線、切換模式、移動操作、感測器狀態列印等完整流程。




