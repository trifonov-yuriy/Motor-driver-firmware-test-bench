import subprocess
import serial.tools.list_ports
import time

def find_arduino_port():
    """Автоматически найти Arduino порт"""
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if 'arduino' in port.description.lower() or 'ch340' in port.description.lower():
            return port.device
    return None

def upload_hex(hex_file):
    # Автоматический поиск порта
    port = find_arduino_port()
    if not port:
        print("Arduino not found! Check connection.")
        return False
    
    print(f"Found Arduino on port: {port}")
    
    # Попробуем разные скорости для надежности
    #baud_rates = [115200, 57600, 19200, 9600]
    baud_rates = [115200, 57600, 19200, 9600]
    for attempt, baud_rate in enumerate(baud_rates, 1):
        print(f"Attempt {attempt}: trying baud rate {baud_rate}...")
        
        try:
            result = subprocess.run([
                'avrdude',
                '-p', 'atmega328p',
                '-c', 'arduino',
                '-P', port,
                '-b', str(baud_rate),
                '-U', f'flash:w:{hex_file}:i'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Upload successful!")
                print(result.stdout)
                return True
            else:
                print(f"❌ Attempt failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print("⚠️  Timeout occurred, trying next baud rate...")
        except Exception as e:
            print(f"⚠️  Error: {e}")
    
    print("❌ All attempts failed!")
    return False

def reset_arduino(port):
    """Попытка сбросить Arduino через Serial"""
    try:
        with serial.Serial(port, 1200, timeout=1) as ser:
            time.sleep(0.5)
        print("Reset signal sent")
        time.sleep(2)  # Ждем перезагрузки
    except:
        pass

if __name__ == "__main__":
    hex_file = 'avr-project.hex'
    
    # Сначала попробуем найти и сбросить Arduino
    port = find_arduino_port()
    if port:
        print(f"Resetting Arduino on {port}...")
        reset_arduino(port)
        time.sleep(2)
    
    # Затем пытаемся прошить
    upload_hex(hex_file)