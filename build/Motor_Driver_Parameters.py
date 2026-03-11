import serial, sys, struct, time
import re
import os
from flask import Flask, request
import codecs
from serial.tools import list_ports
import glob


def get_available_com_ports():
    """
    Возвращает список доступных COM-портов в системе
    """
    ports = serial.tools.list_ports.comports()
    available_ports = []
    
    for port in ports:
        available_ports.append({
            'device': port.device,
            'name': port.name,
            'description': port.description,
            'hwid': port.hwid
        })
    
    return available_ports


def select_com_port():
    """
    Предлагает пользователю выбрать COM-порт из доступных
    """
    available_ports = get_available_com_ports()
    
    if not available_ports:
        print("Не найдено доступных COM-портов!")
        return None
    
    print("\nДоступные COM-порты:")
    for i, port in enumerate(available_ports, 1):
        print(f"{i}. {port['device']} - {port['description']}")
    
    while(True):
        try:
            choice = input("\nВыберите номер порта: ")
            choice_num = int(choice)
            return str(choice_num)
            
        except ValueError:
            print("Пожалуйста, введите число.")
        except KeyboardInterrupt:
            print("\nПрервано пользователем.")
            return None
        

def input_com_port_manually():
    """
    Позволяет пользователю ввести COM-порт вручную
    """
    while True:
        port_input = input("Введите COM-порт (например, COM3): ").strip().upper()
        
        if check_com_port(port_input):
            return port_input
        else:
            print("Неверный формат COM-порта. Используйте формат COMX, где X - номер порта.")



def check_com_port(input_string):
    """
    Проверяет, соответствует ли строка формату COMX, где X - номер порта.
    
    Args:
        input_string (str): Входная строка для проверки
    
    Returns:
        bool: True если соответствует формату, False в противном случае
    """
    # Паттерн: COM + одна или более цифр
    pattern = r'^COM\d+$'
    
    # Проверка соответствия паттерну (регистр не важен)
    if re.match(pattern, input_string, re.IGNORECASE):
        return True
    else:
        return False
    

def is_valid_hex_file(file_path):
    """
    Проверяет, является ли путь корректным для файла с расширением .hex
    
    Args:
        file_path (str): Путь к файлу для проверки
    
    Returns:
        tuple: (bool, str) - (результат проверки, сообщение об ошибке)
    """
    if not file_path:
        return False  #"Путь не может быть пустым"
    
    # Проверяем, что путь не содержит запрещенных символов
    if re.search(r'[<>:"|?*]', file_path):
        return False #"Путь содержит запрещенные символы"
    
    # Проверяем расширение файла
    if not file_path.lower().endswith('.hex'):
        return False #"Файл должен иметь расширение .hex"
    
    # Проверяем, что имя файла не пустое (только расширение)
    file_name = os.path.basename(file_path)
    if file_name == '.hex' or len(file_name) <= 4:
        return False #"Имя файла не может быть пустым"
    
    # Проверяем, что путь существует (если файл уже должен существовать)
    # Раскомментируйте следующую строку, если нужно проверять существование файла:
    # if not os.path.exists(file_path):
    #     return False, "Файл не существует"
    
    # Проверяем, что путь не является директорией
    if os.path.isdir(file_path):
        return False #"Указанный путь является директорией, а не файлом"
    
    return True #"Путь корректен"
    

def get_executable_directory():
    """Определяет директорию исполняемого файла (.exe)"""
    if getattr(sys, 'frozen', False):
        # Если программа 'заморожена' (упакована в exe)
        return os.path.dirname(sys.executable)
    else:
        # Если запущен как обычный Python скрипт
        return os.path.dirname(os.path.abspath(__file__))
    

def find_txt_files(file_name):
    # Получаем путь к директории исполняемого файла
    exe_dir = get_executable_directory()
    #print(f"Ищем в директории: {exe_dir}")
    
    # Ищем все файлы с расширением .txt
    
    text_files = glob.glob(os.path.join(exe_dir, file_name))
    
    return text_files, exe_dir    



class PI():
    def __init__(self, com):
        self.ser = serial.Serial(com, 19200, timeout = 1)

    def get_msg_fromArduino(self):
        while True:
            data = self.ser.read(2)
            if data == b'\xde\xde':
                try:
                    # Читаем до конца строки
                    raw_data = self.ser.read_until(expected=b'\r\n')
                    
                    # Безопасное декодирование с обработкой ошибок
                    try:
                        arduinoDebugString = raw_data.decode('utf-8', errors='replace')
                        print("ARDUINO: ", arduinoDebugString)
                    except UnicodeDecodeError:
                        # Если не UTF-8, показываем как hex
                        hex_string = raw_data.hex(' ', 1).upper()
                        print(f"ARDUINO (hex): {hex_string}")
                        
                except Exception as e:
                    print("get_msg_fromArduino: ", e)
                    
            if data == b'\xc0\xc0':
                try:
                    arduinoCommand = struct.unpack('B', self.ser.read(1))[0]
                    return arduinoCommand
                except Exception as e:
                    print("Error reading command: ", e)
                    return None
          

    def conf(self,):
        # init Programming Interface (PI)     
        while True:
            try:
                print("Try init EFM8...")
                self.ser.write(b'\x01')
                x = self.get_msg_fromArduino()
                print ('x:',hex(x))
                assert(0x81 == x)
                break
            except:
                while self.ser.read(1) != '': pass

        print ('PI initiated')

    def readDump(self, ):
        self.conf()
        #addr = 0x00
        addr = 0x1a00
        while (True):
            addrL = addr & 0xff
            addrH = (addr & 0xff00) >> 8
            header = bytes([0x05, 0x00, 240, 0x00, addrH, addrL])
            self.ser.write(header)
            raw_data = self.ser.read_until(expected=b'\r\n')
            raw_data = self.ser.read_until(expected=b'\r\n')
            while True:
                data = self.ser.read(2)
                if data == b'\xc0\xc0':
                    raw_data = self.ser.read_until(expected=b'\r\n')
                    hex_string = raw_data.hex(' ', 1).upper()
                    if hex_string.endswith('0D 0A'):
                        hex_string = hex_string[:-5]
                    print(hex_string, end = ' ')
                    x = self.get_msg_fromArduino()
                    #print ('x:',hex(x))
                    assert(0x85 == x)       
                    break
                if data == b'\x48\x48':
                    break
                    
            addr = addr + 240
            if(addr > 18000):
                break        

    def read_eeprom_file_to_array(self, filename="eeprom_values.txt"):
        """
        Читает файл с EEPROM значениями и создает массив int_array
        
        Args:
            filename: имя файла для чтения (по умолчанию "eeprom_values.txt")
        
        Returns:
            list: массив целых чисел int_array
        """
        
        # Определяем порядок параметров (такой же как при записи)
        parameters_order = [
            "EEPROM_FW_MAIN_REVISION",
            "EEPROM_FW_SUB_REVISION",
            "EEPROM_LAYOUT_REVISION",
            "_Eep_Pgm_Gov_P_Gain",
            "_Eep_Pgm_Gov_I_Gain",
            "_Eep_Pgm_Gov_Mode",
            "_Eep_Pgm_Low_Voltage_Lim",
            "_Eep_Pgm_Motor_Gain",
            "_Eep_Pgm_Motor_Idle",
            "Eep_Pgm_Startup_Pwr",
            "_Eep_Pgm_Pwm_Freq",
            "Eep_Pgm_Direction",
            "_Eep_Pgm_Input_Pol",
            "Eep_Initialized_L",
            "Eep_Initialized_H",
            "Eep_Enable_TX_Program",
            "_Eep_Main_Rearm_Start",
            "_Eep_Pgm_Gov_Setup_Target",
            "_Eep_Pgm_Startup_Rpm",
            "_Eep_Pgm_Startup_Accel",
            "_Eep_Pgm_Volt_Comp",
            "Eep_Pgm_Comm_Timing",
            "_Eep_Pgm_Damping_Force",
            "_Eep_Pgm_Gov_Range",
            "_Eep_Pgm_Startup_Method",
            "Eep_Pgm_Min_Throttle",
            "Eep_Pgm_Max_Throttle",
            "Eep_Pgm_Beep_Strength",
            "Eep_Pgm_Beacon_Strength",
            "Eep_Pgm_Beacon_Delay",
            "_Eep_Pgm_Throttle_Rate",
            "Eep_Pgm_Demag_Comp",
            "_Eep_Pgm_BEC_Voltage_High",
            "Eep_Pgm_Center_Throttle",
            "_Eep_Pgm_Main_Spoolup_Time",
            "Eep_Pgm_Temp_Prot_Enable",
            "Eep_Pgm_Enable_Power_Prot",
            "_Eep_Pgm_Enable_Pwm_Input",
            "_Eep_Pgm_Pwm_Dither",
            "Eep_Pgm_Brake_On_Stop",
            "Eep_Pgm_LED_Control"
        ]
        
        int_array = [0] * len(parameters_order)  # Создаем массив с нулями
        found_params = set()  # Для отслеживания найденных параметров
        
        try:
            with open(filename, 'r') as file:
                lines = file.readlines()
                
                for line in lines:
                    line = line.strip()
                    if line and ':' in line:
                        # Разделяем строку на имя параметра и значение
                        parts = line.split(':', 1)
                        param_name = parts[0].strip()
                        value_str = parts[1].strip()
                        
                        # Пропускаем строки без значения
                        if not value_str:
                            continue
                        
                        # Преобразуем значение в целое число
                        try:
                            value = int(value_str)
                        except ValueError:
                            print(f"Предупреждение: не удалось преобразовать значение '{value_str}' для параметра '{param_name}'")
                            continue
                        
                        # Находим индекс параметра в нашем порядке
                        if param_name in parameters_order:
                            index = parameters_order.index(param_name)
                            int_array[index] = value
                            found_params.add(param_name)
                        else:
                            print(f"Предупреждение: неизвестный параметр '{param_name}'")
            
            # Проверяем, все ли параметры найдены
            missing_params = set(parameters_order) - found_params
            if missing_params:
                print(f"Предупреждение: следующие параметры не найдены в файле: {missing_params}")
            
            return int_array
            
        except FileNotFoundError:
            print(f"Ошибка: файл {filename} не найден")
            return None
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return None


    def readBlHeliParameters(self, needSave = False, fileName_motor = "eeprom_values.txt"):
        self.conf()
        addr = 0x1a00
        counter = 1
        #byteCnt = 240
        while (True):
            addrL = addr & 0xff
            addrH = (addr & 0xff00) >> 8
            header = bytes([0x05, 0x00, 240, 0x00, addrH, addrL])
            #header = bytes([0x05, 0x00, byteCnt, 0x00, addrH, addrL])
            self.ser.write(header)
            raw_data = self.ser.read_until(expected=b'\r\n')
            raw_data = self.ser.read_until(expected=b'\r\n')
            while True:
                data = self.ser.read(2)
                if data == b'\xc0\xc0':
                    raw_data = self.ser.read_until(expected=b'\r\n')
                    hex_string = raw_data.hex(' ', 1).upper()
                    if hex_string.endswith('0D 0A'):
                        hex_string = hex_string[:-5]
                    print(hex_string, end = ' ')
                    x = self.get_msg_fromArduino()
                    print ('x:',hex(x))
                    assert(0x85 == x)       
                    break
                if data == b'\x48\x48':
                    break
            print("", end = '\r\n')
            if(counter == 1):
                hex_values = hex_string.strip().split()
                int_array = [int(hex_val, 16) for hex_val in hex_values]
                print("EEPROM_FW_MAIN_REVISION:\t", int(int_array[0]))
                print("EEPROM_FW_SUB_REVISION:\t", int(int_array[1]))
                print("EEPROM_LAYOUT_REVISION:\t", int(int_array[2]))
            # print("Eep_FW_Main_Revision: ", int(int_array[3]))
                #print("Eep_FW_Sub_Revision: ", int(int_array[4]))
            # print("Eep_Layout_Revision: ", int(int_array[5]))
                print("_Eep_Pgm_Gov_P_Gain:\t", int(int_array[3]))
                print("_Eep_Pgm_Gov_I_Gain:\t", int(int_array[4]))
                print("_Eep_Pgm_Gov_Mode:\t", int(int_array[5]))
                print("_Eep_Pgm_Low_Voltage_Lim:\t", int(int_array[6]))
                print("_Eep_Pgm_Motor_Gain:\t", int(int_array[7]))
                print("_Eep_Pgm_Motor_Idle:\t", int(int_array[8]))
                print("Eep_Pgm_Startup_Pwr:\t", int(int_array[9]))
                print("_Eep_Pgm_Pwm_Freq:\t", int(int_array[10]))
                print("Eep_Pgm_Direction:\t", int(int_array[11]))
                print("_Eep_Pgm_Input_Pol:\t", int(int_array[12]))
                print("Eep_Initialized_L:\t", int(int_array[13]))
                print("Eep_Initialized_H:\t", int(int_array[14]))
                print("Eep_Enable_TX_Program:\t", int(int_array[15]))
                print("_Eep_Main_Rearm_Start:\t", int(int_array[16]))
                print("_Eep_Pgm_Gov_Setup_Target:\t", int(int_array[17]))
                print("_Eep_Pgm_Startup_Rpm:\t", int(int_array[18]))
                print("_Eep_Pgm_Startup_Accel:\t", int(int_array[19]))
                print("_Eep_Pgm_Volt_Comp:\t", int(int_array[20]))
                print("Eep_Pgm_Comm_Timing:\t", int(int_array[21]))
                print("_Eep_Pgm_Damping_Force:\t", int(int_array[22]))
                print("_Eep_Pgm_Gov_Range:\t", int(int_array[23]))
                print("_Eep_Pgm_Startup_Method:\t", int(int_array[24]))
                print("Eep_Pgm_Min_Throttle:\t", int(int_array[25]))
                print("Eep_Pgm_Max_Throttle:\t", int(int_array[26]))
                print("Eep_Pgm_Beep_Strength:\t", int(int_array[27]))
                print("Eep_Pgm_Beacon_Strength:\t", int(int_array[28]))
                print("Eep_Pgm_Beacon_Delay:\t", int(int_array[29]))
                print("_Eep_Pgm_Throttle_Rate:\t", int(int_array[30]))
                print("Eep_Pgm_Demag_Comp:\t", int(int_array[31]))
                print("_Eep_Pgm_BEC_Voltage_High:\t", int(int_array[32]))
                print("Eep_Pgm_Center_Throttle:\t", int(int_array[33]))
                print("_Eep_Pgm_Main_Spoolup_Time:\t", int(int_array[34]))
                print("Eep_Pgm_Temp_Prot_Enable:\t", int(int_array[35]))
                print("Eep_Pgm_Enable_Power_Prot:\t", int(int_array[36]))
                print("_Eep_Pgm_Enable_Pwm_Input:\t", int(int_array[37]))
                print("_Eep_Pgm_Pwm_Dither:\t", int(int_array[38]))
                print("Eep_Pgm_Brake_On_Stop:\t", int(int_array[39]))
                print("Eep_Pgm_LED_Control:\t", int(int_array[40]))
                if needSave == True:
                    self.create_eeprom_file(int_array, fileName_motor)
            counter = counter + 1
            
            #if(counter > 2):
            #    byteCnt = 32
            #if(counter > 3):
            #    counter = 1
             #   break
            #addr = addr + byteCnt
            return int_array
        

    def create_eeprom_file(self, int_array, filename="eeprom_values.txt"):
        """
        Создает текстовый файл с значениями из массива int_array
        
        Args:
            int_array: массив целых чисел
            filename: имя файла для сохранения (по умолчанию "eeprom_values.txt")
        """
        
        # Определяем названия параметров и их индексы
        parameters = [
            ("EEPROM_FW_MAIN_REVISION", 0),
            ("EEPROM_FW_SUB_REVISION", 1),
            ("EEPROM_LAYOUT_REVISION", 2),
            ("_Eep_Pgm_Gov_P_Gain", 3),
            ("_Eep_Pgm_Gov_I_Gain", 4),
            ("_Eep_Pgm_Gov_Mode", 5),
            ("_Eep_Pgm_Low_Voltage_Lim", 6),
            ("_Eep_Pgm_Motor_Gain", 7),
            ("_Eep_Pgm_Motor_Idle", 8),
            ("Eep_Pgm_Startup_Pwr", 9),
            ("_Eep_Pgm_Pwm_Freq", 10),
            ("Eep_Pgm_Direction", 11),
            ("_Eep_Pgm_Input_Pol", 12),
            ("Eep_Initialized_L", 13),
            ("Eep_Initialized_H", 14),
            ("Eep_Enable_TX_Program", 15),
            ("_Eep_Main_Rearm_Start", 16),
            ("_Eep_Pgm_Gov_Setup_Target", 17),
            ("_Eep_Pgm_Startup_Rpm", 18),
            ("_Eep_Pgm_Startup_Accel", 19),
            ("_Eep_Pgm_Volt_Comp", 20),
            ("Eep_Pgm_Comm_Timing", 21),
            ("_Eep_Pgm_Damping_Force", 22),
            ("_Eep_Pgm_Gov_Range", 23),
            ("_Eep_Pgm_Startup_Method", 24),
            ("Eep_Pgm_Min_Throttle", 25),
            ("Eep_Pgm_Max_Throttle", 26),
            ("Eep_Pgm_Beep_Strength", 27),
            ("Eep_Pgm_Beacon_Strength", 28),
            ("Eep_Pgm_Beacon_Delay", 29),
            ("_Eep_Pgm_Throttle_Rate", 30),
            ("Eep_Pgm_Demag_Comp", 31),
            ("_Eep_Pgm_BEC_Voltage_High", 32),
            ("Eep_Pgm_Center_Throttle", 33),
            ("_Eep_Pgm_Main_Spoolup_Time", 34),
            ("Eep_Pgm_Temp_Prot_Enable", 35),
            ("Eep_Pgm_Enable_Power_Prot", 36),
            ("_Eep_Pgm_Enable_Pwm_Input", 37),
            ("_Eep_Pgm_Pwm_Dither", 38),
            ("Eep_Pgm_Brake_On_Stop", 39),
            ("Eep_Pgm_LED_Control", 40)
        ]
        
        # Создаем файл и записываем данные
        with open(filename, 'w') as file:
            for param_name, index in parameters:
                if index < len(int_array):
                    value = int(int_array[index])
                    # Форматируем строку с выравниванием
                    line = f"{param_name}:\t{value}\n"
                    file.write(line)
        
        print(f"Файл {filename} успешно создан!")


    def writeBlHeliParameters_byArray(self, int_array):
        self.ser.write(b'\x12')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x83 == x)
        time.sleep(0.5)
        print ('Page erased')
        addr = 0x1a00
        #for value in int_array:
        addrh = (addr & 0xff00) >> 8
        addrl = addr & 0x00ff

        crc = (addrh + addrl) & 0xff
        buf_size = 240
        buf_hex = bytes(int_array)  # вместо codecs.decode(buf, 'hex')
        crc += sum(buf_hex)
        header = bytes([0x11, buf_size + 7, buf_size, 0, addrh, addrl, crc & 0xff])
        self.ser.write(header)
        self.ser.write(buf_hex)         
        ret = self.get_msg_fromArduino()
        if ret == 0x83:
            print ('Write SUCCESS ')
        else:
            print ('error flash write returned ', hex(ret))
            raise RuntimeError('bad crc')   
        addr = addr + 1

        self.ser.write(b'\x02')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x82 == x)

        # reset device
        self.ser.write(b'\x02')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x82 == x)        

        # reset device
        self.ser.write(b'\x02')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x82 == x)      

    def writeBlHeliParameters(self, parameters):
        self.ser.write(b'\x12')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x83 == x)
        time.sleep(0.5)
        print ('Page erased')

        for addr, value in parameters.items():
            addrh = (addr & 0xff00) >> 8
            addrl = addr & 0x00ff

            crc = (addrh + addrl) & 0xff
            buf_size = 1
            buf_hex = bytes([value])  # вместо codecs.decode(buf, 'hex')
            crc += sum(buf_hex)
            header = bytes([0x11, buf_size + 7, buf_size, 0, addrh, addrl, crc & 0xff])
            self.ser.write(header)
            self.ser.write(buf_hex)         
            ret = self.get_msg_fromArduino()
            if ret == 0x83:
                print ('Write SUCCESS ')
            else:
                print ('error flash write returned ', hex(ret))
                raise RuntimeError('bad crc')    
            
    def readHexFile(self, filePath):
        with open(filePath, 'r') as file:
            firmware = file.read()  # Читаем весь файл как одну строку    
        f = firmware.splitlines()

        total = 0
        buf = ''
        buf_size = 0
        addr_solve = 0
        addr_solve_prev = 0

        for i in f[1:-1]:  # skip first and second lines
                    addr_solve_prev = addr_solve
                    assert(i[0] == ':')
                    size = int(i[1:3],16)
                    assert(size + 4 < 256)
                    if buf_size == 0:
                        addrh = int(i[3:5],16)
                        addrl = int(i[5:7],16)
                        addr = addrh << 8 | addrl
                    addr_solve = int(i[3:5],16) << 8 | int(i[5:7],16)
                    assert(i[7:9] == '00')
                    data = i[9:9 + size*2]
                    assert(len(data) == size*2)

                    buf += data
                    buf_size += size     
                    if(addr_solve_prev != addr_solve - size):
                        buf_size = 0

    def prog_motor_1(self, filePath):
        self.ser.write(b'\x13')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)

        print ('Choose motor_1')        
        

        self.prog(filePath)
        self.readBlHeliParameters(needSave=True, fileName_motor="eeprom_values_motor_1.txt")
        

    def prog_motor_2(self, filePath):
        self.ser.write(b'\x14')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)

        print ('Choose motor_2')       

        self.prog(filePath) 
        self.readBlHeliParameters(needSave=True, fileName_motor="eeprom_values_motor_2.txt")
        

    def prog_motor_3(self, filePath):
        self.ser.write(b'\x15')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)

        print ('Choose motor_3')     

        self.prog(filePath)   
        self.readBlHeliParameters(needSave=True, fileName_motor="eeprom_values_motor_3.txt")
        

    def prog_motor_4(self, filePath):
        self.ser.write(b'\x16')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)
        print ('Choose motor_4')        

        self.prog(filePath)
        self.readBlHeliParameters(needSave=True, fileName_motor="eeprom_values_motor_4.txt")

    def read_motor(self, filePath):
        #Чтение и запись в файл
        int_array = self.readBlHeliParameters()
        int_array_readFromFile = self.read_eeprom_file_to_array(filePath)
        i = 0
        for value in int_array_readFromFile:
            int_array[i] = value
            i = i + 1

        self.writeBlHeliParameters_byArray(int_array)
        self.readBlHeliParameters(True, filePath)        

    def read_motor_1(self, filePath):
        self.ser.write(b'\x13')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)
        print ('Choose motor_1')   
        self.conf()    
        self.read_motor(filePath)

    def read_motor_2(self, filePath):
        self.ser.write(b'\x14')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)
        print ('Choose motor_2')  
        self.conf()    
        self.read_motor(filePath)


    def read_motor_3(self, filePath):
        self.ser.write(b'\x15')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)
        print ('Choose motor_3')
        self.conf()    
        self.read_motor(filePath)

    def read_motor_4(self, filePath):
        self.ser.write(b'\x16')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)
        print ('Choose motor_4')   
        self.conf()       
        self.read_motor(filePath)          
                

    def prog(self, filePath):
        with open(filePath, 'r') as file:
            firmware = file.read()  # Читаем весь файл как одну строку
        print ('Connected')

        #f = open(firmware,'r').readlines()
        f = firmware.splitlines()

        self.conf()

        # erase device
        self.ser.write(b'\x04')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x84 == x)

        print ('Device erased')

        # write hex file
        total = 0
        buf = ''
        buf_size = 0
        addr_solve = 0
        addr_solve_prev = 0
        for i in f[1:-1]:  # skip first and second lines
            addr_solve_prev = addr_solve
            assert(i[0] == ':')
            size = int(i[1:3],16)
            assert(size + 4 < 256)
            if buf_size == 0:
                addrh = int(i[3:5],16)
                addrl = int(i[5:7],16)
            addr_solve = int(i[3:5],16) << 8 | int(i[5:7],16)
            assert(i[7:9] == '00')
            data = i[9:9 + size*2]
            assert(len(data) == size*2)

            buf += data
            buf_size += size

            if buf_size > 256 - 0x20 or i == f[-2] or (addr_solve_prev != addr_solve - size):
                attempts = 0
                while True:
                    try:
                        
                        crc = (addrh + addrl) & 0xff
                        #buf_hex = codecs.decode(buf, 'hex')
                        # ИСПРАВЛЕНИЕ 1: Преобразование hex-строки в байты
                        buf_hex = bytes.fromhex(buf)  # вместо codecs.decode(buf, 'hex')
                        #crc += sum([struct.unpack('B', x)[0] for x in buf_hex])
                        # ИСПРАВЛЕНИЕ 2: Правильное вычисление суммы байт
                        crc += sum(buf_hex)  # buf_hex уже байты, не нужно распаковывать
                        #assert(len(buf.decode('hex')) == buf_size)
                        # ИСПРАВЛЕНИЕ 3: Проверка длины (альтернативный способ)
                        assert(len(buf_hex) == buf_size)
                        #self.ser.write([0x3, buf_size + 4 + 1, buf_size, 0, addrh, addrl, crc & 0xff])
                        #self.ser.write(buf_hex)
                        # ИСПРАВЛЕНИЕ 4: Правильная запись в порт
                        # Создаем bytes объект для записи
                        
                        header = bytes([0x03, buf_size + 7, buf_size, 0, addrh, addrl, crc & 0xff])
                        print("address: ", (addrh << 8) | addrl)
                        print (header)
                        print(buf)
                        self.ser.write(header)
                        self.ser.write(buf_hex)

                        ret = self.get_msg_fromArduino()
                        if ret == 0x83:
                            pass
                        else:
                            print ('error flash write returned ', hex(ret))
                            raise RuntimeError('bad crc')
                        break
                    except Exception as e:
                        print (e)
                        print ('attempts:',attempts)
                        attempts += 1
                        self.conf()
                            
                print ('Wrote %d bytes block' % buf_size)
                total += buf_size
                buf_size = 0
                buf = ''
                
                print ('Wrote %d bytes' % total)


        # reset device
        self.ser.write(b'\x02')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x82 == x)

        # reset device
        self.ser.write(b'\x02')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x82 == x)        

        # reset device
        self.ser.write(b'\x02')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x82 == x)      



        print ('Device reset')



def main():
    try:
        port = select_com_port()
        port = "COM" + port
        programmer = PI(port)
        time.sleep(2)

        motor_1_file = find_txt_files('eeprom_values_motor_1.txt')[0]
        motor_2_file = find_txt_files('eeprom_values_motor_2.txt')[0]
        motor_3_file = find_txt_files('eeprom_values_motor_3.txt')[0]
        motor_4_file = find_txt_files('eeprom_values_motor_4.txt')[0]

        programmer.read_motor_1(motor_1_file[0])
        programmer.read_motor_2(motor_2_file[0])
        programmer.read_motor_3(motor_3_file[0])
        programmer.read_motor_4(motor_4_file[0])

    except Exception as e:
        print(e)

    return
    return
    try:
        port = input("Введите номер порта: ")
        port = "COM" + port
        programmer = PI(port)
        print("Убедитесь, что файлы прошивки .hex лежат в той же директории, что и текущий исполняемый файл")
        while(True):
            input("Для выполнения прошивки нажмите Enter")
           
            #programmer.readHexFile("A_H_0_REV16_7.HEX")
            programmer.conf()
            #programmer.readDump()

            #Прошивка и запись в файл параметров
            
            programmer.prog_motor_1("A_H_0_REV16_7.HEX")
            programmer.prog_motor_2("A_H_0_REV16_7.HEX")
            programmer.prog_motor_3("A_H_0_REV16_7.HEX")
            programmer.prog_motor_4("A_H_0_REV16_7.HEX")
    except Exception as e:
        print(e)



    return

    #Чтение и запись в файл
    int_array = programmer.readBlHeliParameters()
    int_array_readFromFile = programmer.read_eeprom_file_to_array()

    i = 0
    for value in int_array_readFromFile:
        int_array[i] = value
        i = i + 1

    programmer.writeBlHeliParameters_byArray(int_array)
    programmer.readBlHeliParameters(needSave=True)

    return
    
    #addr = 0x1a00
    #parameters = {
    #    addr + 9: 10, 
    #    addr + 11: 1, 
    #    addr + 13: 85, 
    #    addr + 14: 187, 
    #    addr + 15: 1, 
    #    addr + 21: 3,
    #    addr + 25: 37,
    #    addr + 26: 208,
    #    addr + 27: 40,
    #   addr + 28: 80
    #    }    
    

    return

    if len(sys.argv) < 3:
        print('Укажите com-порт в формате COMX, где X - номер порта')
        print('И путь к hex-файлу прошивки')
        sys.exit(1)

    if len(sys.argv) < 2:
        print ('usage: %s <port> <serial-port1> [serial-port2...]' % sys.argv[0])
        sys.exit(1)

    if check_com_port(sys.argv[1]) == False:
        print('Укажите com-порт в формате COMX, где X - номер порта')
        sys.exit(1)

    if is_valid_hex_file(sys.argv[2]) == False:
        print('Укажите правильный путь к hex-файлу прошивки')
        sys.exit(1)    


    programmer = PI(sys.argv[1])
    programmer.conf()
    programmer.prog(sys.argv[2])

        
if __name__ == "__main__":
    main()
