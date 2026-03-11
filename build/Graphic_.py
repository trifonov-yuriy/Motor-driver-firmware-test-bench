import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import sys
import os
import serial
import serial.tools.list_ports
import time
import sys, struct


class PI():
    def __init__(self, comport):
        self.ser = comport

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
                    
            elif data == b'\xc0\xc0':
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


    def motor_low_sound(self, filePath):
        #Чтение и запись в файл
        int_array = self.readBlHeliParameters()
        int_array_readFromFile = self.read_eeprom_file_to_array(filePath)
        i = 0
        for value in int_array_readFromFile:
            int_array[i] = value
            i = i + 1
        int_array[27] = 1
        self.writeBlHeliParameters_byArray(int_array)
        self.readBlHeliParameters(True, filePath)

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

    def Start_motor_1(self, throttle):
        for_write = bytes([0xe1, throttle])
        self.ser.write(for_write)

    def Start_motor_2(self, throttle):
        for_write = bytes([0xe2, throttle])
        self.ser.write(for_write)

    def Start_motor_3(self, throttle):
        for_write = bytes([0xe3, throttle])
        self.ser.write(for_write)          

    def Start_motor_4(self, throttle):
        for_write = bytes([0xe4, throttle])
        self.ser.write(for_write)

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

    
    def float_from_components(self, sign, exponent, mantissa_high, mantissa_mid, mantissa_low, byte_order='little'):
        """
        Упрощенная версия через прямое битовое представление
        """

        sign = int(sign) & 0x1
        exponent = int(exponent) & 0xFF
        mantissa_high = int(mantissa_high) & 0xFF
        mantissa_mid = int(mantissa_mid) & 0xFF
        mantissa_low = int(mantissa_low) & 0xFF

        # Собираем полную мантиссу (23 бита)
        mantissa_full = (mantissa_high << 16) | (mantissa_mid << 8) | mantissa_low
        mantissa_full &= 0x7FFFFF  # Оставляем только 23 бита
        
        # Собираем 32-битное представление IEEE 754
        float_bits = (sign << 31) | (exponent << 23) | mantissa_full
        
      #  print(f"32-битное представление: 0x{float_bits:08X}")
        
        # Преобразуем в байты (little-endian)
        bytes_data = float_bits.to_bytes(4, byteorder='little')
      #  print(f"Байты: {[hex(b) for b in bytes_data]}")
        
        # Преобразуем в float
        value = struct.unpack('f', bytes_data)[0]
        return value
    
    def disable_pwr_check(self):
        self.ser.write(b'\x1a')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)    

    def enable_pwr(self):
        self.ser.write(b'\x17')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)            


    def calibration(self):
        self.ser.write(b'\xe0')

    def disable_pwr(self):
        self.ser.write(b'\x18')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)         

    def enable_pwr_check(self):
        self.ser.write(b'\x19')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)    

    def give_current(self):
        self.ser.write(b'\xc1')
        self.ser.reset_input_buffer()
        datas = self.ser.read(5)
        sign = datas[0]
        exponent = datas[1]
        mantissa_high = datas[2]
        mantissa_mid = datas[3]
        mantissa_low = datas[4]
        I = self.float_from_components(sign, exponent, mantissa_high, mantissa_mid, mantissa_low)
        print("I=", I)
        return I


    def check_current(self):
        self.ser.write(b'\x1c')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)             
        sign = self.get_msg_fromArduino()
        exponent = self.get_msg_fromArduino()
        mantissa_high = self.get_msg_fromArduino()
        mantissa_mid = self.get_msg_fromArduino()
        mantissa_low = self.get_msg_fromArduino()
        U = self.float_from_components(sign, exponent, mantissa_high, mantissa_mid, mantissa_low)     
        print("U=", U)   
        
        sign = self.get_msg_fromArduino()
        exponent = self.get_msg_fromArduino()
        mantissa_high = self.get_msg_fromArduino()
        mantissa_mid = self.get_msg_fromArduino()
        mantissa_low = self.get_msg_fromArduino()
        I = self.float_from_components(sign, exponent, mantissa_high, mantissa_mid, mantissa_low)
        print("I=", I)
        return I
    

    def check_pwr(self):
        self.ser.write(b'\x1b')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)      

        sign = self.get_msg_fromArduino()
        exponent = self.get_msg_fromArduino()
        mantissa_high = self.get_msg_fromArduino()
        mantissa_mid = self.get_msg_fromArduino()
        mantissa_low = self.get_msg_fromArduino()
        U = self.float_from_components(sign, exponent, mantissa_high, mantissa_mid, mantissa_low)     
        print("U=", U)   
        
        sign = self.get_msg_fromArduino()
        exponent = self.get_msg_fromArduino()
        mantissa_high = self.get_msg_fromArduino()
        mantissa_mid = self.get_msg_fromArduino()
        mantissa_low = self.get_msg_fromArduino()
        I = self.float_from_components(sign, exponent, mantissa_high, mantissa_mid, mantissa_low)
        print("I=", I)
        return I


    def prog_motor_1(self, filePath):
        self.ser.write(b'\x13')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)

        print ('Choose motor_1')   

        self.conf()     
        

        self.prog(filePath)
        self.readBlHeliParameters(needSave=True, fileName_motor="eeprom_values_motor_1.txt")
        self.motor_low_sound("eeprom_values_motor_1.txt")
        

    def prog_motor_2(self, filePath):
        self.ser.write(b'\x14')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)

        print ('Choose motor_2')       

        self.conf()  
        self.prog(filePath) 
        self.readBlHeliParameters(needSave=True, fileName_motor="eeprom_values_motor_2.txt")
        self.motor_low_sound("eeprom_values_motor_2.txt")

    def prog_motor_3(self, filePath):
        self.ser.write(b'\x15')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)

        print ('Choose motor_3')     

        self.conf()  
        self.prog(filePath)   
        self.readBlHeliParameters(needSave=True, fileName_motor="eeprom_values_motor_3.txt")
        self.motor_low_sound("eeprom_values_motor_3.txt")

    def prog_motor_4(self, filePath):
        self.ser.write(b'\x16')
        x = self.get_msg_fromArduino()
        print ('x:',hex(x))
        assert(0x80 == x)

        print ('Choose motor_4')        

        self.conf()  
        self.prog(filePath)
        self.readBlHeliParameters(needSave=True, fileName_motor="eeprom_values_motor_4.txt")
        self.motor_low_sound("eeprom_values_motor_4.txt")
                

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


class MotorControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Стенд прошивки драйвера моторов")
        self.root.geometry("800x900")
        
        # Переменные для COM-порта
        self.serial_connection = None
        self.is_connected = False
        self.selected_port = None

        self.engine_1_status = 0
        self.engine_2_status = 0
        self.engine_3_status = 0
        self.engine_4_status = 0

        self.monitoring_status = 0
        
        # Переменные для тяги двигателей
        self.thrust_values = [tk.IntVar(value=0) for _ in range(4)]  # Значения тяги для 4 двигателей
        
        # Создаем консоль
        self.setup_console()
        
        # Создаем интерфейс
        self.setup_ui()
        
        # Автоматическое обнаружение портов при запуске
        self.refresh_ports()
        
    def setup_console(self):
        """Настройка консольного вывода"""
        print("=" * 50)
        print("Система управления двигателями запущена")
        print("Графический интерфейс инициализирован")
        print("=" * 50)
        
    def setup_ui(self):
        """Создание графического интерфейса"""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Стенд прошивки драйвера моторов", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Фрейм для COM-порта
        com_frame = ttk.LabelFrame(main_frame, text="Подключение к COM-порту", padding="10")
        com_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Выбор COM-порта
        ttk.Label(com_frame, text="COM-порт:").grid(row=0, column=0, padx=(0, 5))
        
        self.port_combobox = ttk.Combobox(com_frame, width=15, state="readonly")
        self.port_combobox.grid(row=0, column=1, padx=5)
        
        self.refresh_ports_btn = ttk.Button(
            com_frame, 
            text="Обновить порты", 
            command=self.refresh_ports
        )
        self.refresh_ports_btn.grid(row=0, column=2, padx=5)
        
        # Настройки подключения
        ttk.Label(com_frame, text="Скорость:").grid(row=0, column=3, padx=(20, 5))
        
        self.baud_combobox = ttk.Combobox(com_frame, width=10, values=["9600", "115200", "57600", "38400", "19200"])
        self.baud_combobox.set("19200")
        self.baud_combobox.grid(row=0, column=4, padx=5)
        
        # Кнопки подключения/отключения
        self.connect_btn = ttk.Button(
            com_frame, 
            text="Подключиться", 
            command=self.connect_serial
        )
        self.connect_btn.grid(row=0, column=5, padx=5)
        
        self.disconnect_btn = ttk.Button(
            com_frame, 
            text="Отключиться", 
            command=self.disconnect_serial,
            state="disabled"
        )
        self.disconnect_btn.grid(row=0, column=6, padx=5)
        
        # Статус подключения
        self.connection_status = ttk.Label(com_frame, text="Не подключено", foreground="red")
        self.connection_status.grid(row=1, column=0, columnspan=7, pady=(5, 0))
        
        # Кнопки общего назначения
        common_frame = ttk.LabelFrame(main_frame, text="Общие операции", padding="10")
        common_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.check_short_circuit_btn = ttk.Button(
            common_frame, 
            text="Выполнить проверку на КЗ", 
            command=self.check_short_circuit
        )
        self.check_short_circuit_btn.grid(row=0, column=0, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.flash_firmware_btn = ttk.Button(
            common_frame, 
            text="Выполнить прошивку", 
            command=self.flash_firmware
        )

        self.flash_firmware_btn.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.supply_voltage_btn = ttk.Button(
            common_frame, 
            text="Подать питание на драйвер", 
            command=self.supply_voltage
        )  

        self.supply_voltage_btn.grid(row=0, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.supply_voltage_and_calibration_btn = ttk.Button(
            common_frame, 
            text="Подать питание на драйвер с калибровкой", 
            command=self.supply_voltage_and_calibration
        )          

        self.supply_voltage_and_calibration_btn.grid(row=1, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.disable_supply_voltage_btn = ttk.Button(
            common_frame, 
            text="Отключить питание драйвера", 
            command=self.disable_supply_voltage
        )  
        self.disable_supply_voltage_btn.grid(row=2, column=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        common_frame.columnconfigure(0, weight=1)
        common_frame.columnconfigure(1, weight=1)
        common_frame.columnconfigure(2, weight=1)
        common_frame.columnconfigure(3, weight=1)
        
        # Фрейм для управления двигателями
        motors_frame = ttk.LabelFrame(main_frame, text="Управление двигателями", padding="10")
        motors_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Создаем кнопки для каждого двигателя
        self.motor_buttons = []
        for i in range(4):
            motor_num = i + 1
            
            # Фрейм для одного двигателя
            motor_frame = ttk.Frame(motors_frame)
            motor_frame.grid(row=i, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
            
            # Кнопка изменения параметров
            params_btn = ttk.Button(
                motor_frame,
                text=f"Изменить параметры двигателя №{motor_num}",
                command=lambda num=motor_num: self.change_motor_parameters(num)
            )
            params_btn.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))

            params_btn = ttk.Button(
                motor_frame,
                text=f"Открыть файл параметров двигателя №{motor_num}",
                command=lambda num=motor_num: self.open_motor_parameters_file(num)
            )
            params_btn.grid(row=1, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
            
            # Фрейм для управления тягой
            thrust_frame = ttk.Frame(motor_frame)
            thrust_frame.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
            
            # Метка для значения тяги
            thrust_label = ttk.Label(thrust_frame, text="Тяга:")
            thrust_label.grid(row=0, column=0, padx=(0, 5))
            
            # Ползунок для тяги
            thrust_scale = ttk.Scale(
                thrust_frame,
                from_=0,
                to=100,
                orient=tk.HORIZONTAL,
                variable=self.thrust_values[i],
                length=150,
                command=lambda value, num=motor_num: self.on_thrust_change(num, value)
            )
            thrust_scale.grid(row=0, column=1, padx=5)
            
            # Поле для отображения значения тяги
            thrust_value_label = ttk.Label(thrust_frame, textvariable=self.thrust_values[i], width=3)
            thrust_value_label.grid(row=0, column=2, padx=5)
            
            # Кнопка запуска двигателя
            start_btn = ttk.Button(
                motor_frame,
                text=f"Запустить двигатель №{motor_num}",
                command=lambda num=motor_num: self.start_motor(num)
            )
            start_btn.grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E))

            stop_btn = ttk.Button(
                motor_frame,
                text=f"Остановить двигатель №{motor_num}",
                command=lambda num=motor_num: self.stop_motor(num)
            )
            stop_btn.grid(row=1, column=2, padx=(5, 0), sticky=(tk.W, tk.E))
            
            motor_frame.columnconfigure(0, weight=1)
            motor_frame.columnconfigure(1, weight=0)
            motor_frame.columnconfigure(2, weight=1)
            thrust_frame.columnconfigure(1, weight=1)
            
            self.motor_buttons.append((params_btn, start_btn, stop_btn, thrust_scale))
        
        # Фрейм для мониторинга данных
        monitor_frame = ttk.LabelFrame(main_frame, text="Мониторинг данных", padding="10")
        monitor_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.monitor_text = tk.Text(monitor_frame, height=8, width=80)
        scrollbar = ttk.Scrollbar(monitor_frame, orient="vertical", command=self.monitor_text.yview)
        self.monitor_text.configure(yscrollcommand=scrollbar.set)
        
        self.monitor_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Кнопки для мониторинга
        monitor_buttons_frame = ttk.Frame(monitor_frame)
        monitor_buttons_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(monitor_buttons_frame, text="Очистить", 
                  command=self.clear_monitor).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(monitor_buttons_frame, text="Тестовый запрос", 
                  command=self.send_test_command).pack(side=tk.LEFT)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Система готова к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Настройка весов строк и столбцов
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        motors_frame.columnconfigure(0, weight=1)
        motors_frame.columnconfigure(1, weight=0)
        motors_frame.columnconfigure(2, weight=1)
        monitor_frame.columnconfigure(0, weight=1)
        monitor_frame.rowconfigure(0, weight=1)
        
    def on_thrust_change(self, motor_number, value):
        """Обработчик изменения положения ползунка тяги"""
        thrust_value = int(float(value))
        self.thrust_values[motor_number-1].set(thrust_value)
        print(f"Двигатель {motor_number}: установлена тяга {thrust_value}")
        programmer = PI(self.serial_connection)
        if(motor_number == 1):
            if(self.engine_1_status == 1):
                programmer.Start_motor_1(thrust_value)
        elif(motor_number == 2):
            if(self.engine_2_status == 1):
                programmer.Start_motor_2(thrust_value)
        elif(motor_number == 3):
            if(self.engine_3_status == 1):
                programmer.Start_motor_3(thrust_value)       
        elif(motor_number == 4):
            if(self.engine_4_status == 1):
                programmer.Start_motor_4(thrust_value)     




        
    def refresh_ports(self):
        """Обновление списка доступных COM-портов"""
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device} - {port.description}" for port in ports]
        
        self.port_combobox['values'] = port_list
        if port_list:
            self.port_combobox.set(port_list[0])
            print(f"Найдены COM-порты: {[port.device for port in ports]}")
        else:
            print("COM-порты не обнаружены")
            self.port_combobox.set('')
    
    def connect_serial(self):
        """Подключение к выбранному COM-порту"""
        if not self.port_combobox.get():
            messagebox.showerror("Ошибка", "Выберите COM-порт для подключения")
            return
        
        try:
            # Извлекаем имя порта из строки (формат: "COM3 - Описание")
            port_name = self.port_combobox.get().split(' - ')[0]
            baud_rate = int(self.baud_combobox.get())
            
            print(f"Подключение к {port_name} на скорости {baud_rate}...")
            self.serial_connection = serial.Serial(port_name, baud_rate, timeout = 1)
            
            self.is_connected = True
            self.selected_port = port_name
            
            # Обновляем интерфейс
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            self.port_combobox.config(state="disabled")
            self.baud_combobox.config(state="disabled")
            self.connection_status.config(text=f"Подключено к {port_name}", foreground="green")
            
            self.status_var.set(f"Подключено к {port_name}")
            print(f"Успешное подключение к {port_name}")
            
            
        except serial.SerialException as e:
            messagebox.showerror("Ошибка подключения", f"Не удалось подключиться к {port_name}:\n{str(e)}")
            print(f"Ошибка подключения: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка:\n{str(e)}")
            print(f"Неизвестная ошибка: {e}")
    
    def disconnect_serial(self):
        """Отключение от COM-порта"""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                self.is_connected = False
                
                # Обновляем интерфейс
                self.connect_btn.config(state="normal")
                self.disconnect_btn.config(state="disabled")
                self.port_combobox.config(state="readonly")
                self.baud_combobox.config(state="readonly")
                self.connection_status.config(text="Не подключено", foreground="red")
                
                self.status_var.set("Отключено от COM-порта")
                print(f"Отключено от {self.selected_port}")
                self.selected_port = None
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при отключении:\n{str(e)}")
                print(f"Ошибка отключения: {e}")
    
    
    def display_serial_data(self, data):
        """Отображение данных в мониторе"""
        def update_display():
            self.monitor_text.insert(tk.END, data + "\n")
            self.monitor_text.see(tk.END)
        
        # Обновляем из главного потока tkinter
        self.root.after(0, update_display)
    
    def send_serial_data(self, data):
        """Отправка данных через COM-порт"""
        if not self.is_connected or not self.serial_connection:
            messagebox.showwarning("Предупреждение", "Нет подключения к COM-порту")
            return False
        
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            self.serial_connection.write(data)
            self.display_serial_data(f"→ {data.decode('utf-8', errors='ignore')}")
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка отправки данных:\n{str(e)}")
            print(f"Ошибка отправки: {e}")
            return False
    
    def send_test_command(self):
        """Отправка тестовой команды"""
        if self.send_serial_data("TEST\n"):
            print("Отправлена тестовая команда")
    
    def clear_monitor(self):
        """Очистка монитора данных"""
        self.monitor_text.delete(1.0, tk.END)
    
    def check_short_circuit(self):
        """Проверка на короткое замыкание"""
        print("Выполняется проверка на короткое замыкание...")
        self.status_var.set("Выполняется проверка на КЗ...")
        
        # Здесь будет ваша функция проверки КЗ
        
        if(self.empty_function_short_circuit() == 1):
            self.status_var.set("Обнаружено КЗ!!!")

    def disable_supply_voltage(self):
        print("Отключение питания драйвера...")
        # Здесь будет ваша функция прошивки
        self.empty_function_disable_supply_voltage()        

    def supply_voltage(self):
        """Прошивка firmware"""
        print("Подача питания на драйвер...")
        # Здесь будет ваша функция прошивки
        self.empty_function_supply_voltage()
        
    def supply_voltage_and_calibration(self):
        """Прошивка firmware"""
        print("Подача питания на драйвер и калибровка")
        # Здесь будет ваша функция прошивки
        self.empty_function_supply_voltage_and_calibration()
            
    def flash_firmware(self):
        """Прошивка firmware"""
        print("Запуск процесса прошивки...")
        self.status_var.set("Выбор файла прошивки...")
        
        # Диалог выбора файла
        file_path = filedialog.askopenfilename(
            title="Выберите файл прошивки",
            filetypes=[("Hex files", "*.hex"), ("All files", "*.*")]
        )
        
        if file_path:
            print(f"Выбран файл: {file_path}")
            self.status_var.set(f"Прошивка из файла: {os.path.basename(file_path)}")
            
            # Здесь будет ваша функция прошивки
            self.empty_function_flash_firmware(file_path)
        else:
            print("Файл не выбран")
            self.status_var.set("Прошивка отменена")
        
    def open_motor_parameters_file(self, motor_number):
        """Файл параметров двигателя"""
        print(f"Файл параметров двигателя №{motor_number}")
        self.status_var.set(f"Файл параметров двигателя №{motor_number}")
        
        # Формируем имя файла в зависимости от номера двигателя
        filename = f"eeprom_values_motor_{motor_number}.txt"
        
        try:
            # Получаем путь к директории, где находится исполняемый файл
            if getattr(sys, 'frozen', False):
                # Если приложение собрано в exe (pyinstaller)
                application_path = os.path.dirname(sys.executable)
            else:
                # Если запущено как Python скрипт
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            # Формируем полный путь к файлу
            file_path = os.path.join(application_path, filename)
            
            # Проверяем существование файла
            if os.path.exists(file_path):
                # Открываем файл с помощью стандартного приложения ОС
                if os.name == 'nt':  # Windows
                    os.startfile(file_path)
                elif os.name == 'posix':  # Linux, macOS
                    import subprocess
                    opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                    subprocess.call([opener, file_path])
                
                print(f"Файл {filename} успешно открыт")
                self.status_var.set(f"Файл {filename} открыт")
            else:
                print(f"Файл {filename} не найден в директории приложения")
                self.status_var.set(f"Файл {filename} не найден")
                messagebox.showwarning("Файл не найден", 
                                    f"Файл {filename} не найден в директории приложения.\n"
                                    f"Путь: {application_path}")
        
        except Exception as e:
            error_msg = f"Ошибка при открытии файла: {str(e)}"
            print(error_msg)
            self.status_var.set("Ошибка открытия файла")
            messagebox.showerror("Ошибка", error_msg)
      
    def change_motor_parameters(self, motor_number):
        """Изменение параметров двигателя"""
        print(f"Изменение параметров двигателя №{motor_number}")
        self.status_var.set(f"Изменение параметров двигателя №{motor_number}")
        
        
        # Здесь будет ваша функция изменения параметров
        self.empty_function_change_parameters(motor_number)
        
    def stop_motor(self, motor_number):
        """Останов двигателя"""
        print(f"Останов двигателя №{motor_number}")
        self.status_var.set(f"Останов двигателя №{motor_number}")
        self.empty_function_stop_motor(motor_number)


    def start_motor(self, motor_number):
        """Запуск двигателя"""
        thrust_value = self.thrust_values[motor_number-1].get()
        print(f"Запуск двигателя №{motor_number} с тягой {thrust_value}")
        self.status_var.set(f"Запуск двигателя №{motor_number} (тяга: {thrust_value})")
        
        
        # Здесь будет ваша функция запуска двигателя
        self.empty_function_start_motor(motor_number, thrust_value)

    def start_periodic_monitoring(self):
        """Запуск периодического мониторинга состояния двигателей"""
        def monitor_current():
            if self.is_connected:
                try:
                    # Проверка напряжения и тока
                    programmer = PI(self.serial_connection)
                    I = programmer.give_current()
                    
                    # Обновление статуса
                    status_text = f"Ток: {I:.2f}A"
                    self.status_var.set(status_text)
                    
                    # Логирование в монитор
                    self.display_serial_data(f"Мониторинг: {status_text}")
                    
                    # Проверка на перегрузку
                    if I > 20.0:  # Пример порога перегрузки
                        self.display_serial_data("⚠️ ПРЕДУПРЕЖДЕНИЕ: Перегрузка по току!")
                    
                except Exception as e:
                    print(f"Ошибка мониторинга: {e}")
        
        # Запускаем таймер каждые 0,5 секунд
        self.monitoring_timer = self.root.after(500, self.start_periodic_monitoring)
        monitor_current()

    def stop_periodic_monitoring(self):
        """Остановка периодического мониторинга"""
        if hasattr(self, 'monitoring_timer'):
            self.root.after_cancel(self.monitoring_timer)
            print("Мониторинг остановлен")


    # Пустые функции для дальнейшей реализации
    def empty_function_short_circuit(self):
        """Пустая функция проверки КЗ"""
        programmer = PI(self.serial_connection)
        time.sleep(2)
        programmer.enable_pwr_check()
        time.sleep(1)
        i = 0
        for i in range(0, 50):
            I = programmer.check_pwr()
            time.sleep(0.01)
        if I > 0.05:
            programmer.disable_pwr_check()
            print("Утечка!")
            return 1
                
        return 0

    def empty_function_disable_supply_voltage(self):
        print(f"Отключения питания драйвера моторов")
        programmer = PI(self.serial_connection)
        programmer.disable_pwr()
        pass
    
    def empty_function_supply_voltage(self):
        print(f"Подача питания на драйвер моторов")
        programmer = PI(self.serial_connection)
        time.sleep(2)
        programmer.disable_pwr_check()
        time.sleep(1)
        programmer.enable_pwr()
        pass

    def empty_function_supply_voltage_and_calibration(self):
        print(f"Подача питания на драйвер моторов")
        programmer = PI(self.serial_connection)
        time.sleep(2)
        programmer.calibration()
        pass

    def empty_function_flash_firmware(self, file_path):
        """Пустая функция прошивки"""
        print(f"Выполняется прошивка из файла: {file_path}")
        programmer = PI(self.serial_connection)
        time.sleep(2)
        programmer.prog_motor_1(file_path)
        programmer.prog_motor_2(file_path)
        programmer.prog_motor_3(file_path)
        programmer.prog_motor_4(file_path)
        # Ваш код прошивки будет здесь
        
    def empty_function_change_parameters(self, motor_number):
        """Пустая функция изменения параметров"""
        # Проверяем существование файла
        # Формируем имя файла в зависимости от номера двигателя
        filename = f"eeprom_values_motor_{motor_number}.txt"
        
        try:
            # Получаем путь к директории, где находится исполняемый файл
            if getattr(sys, 'frozen', False):
                # Если приложение собрано в exe (pyinstaller)
                application_path = os.path.dirname(sys.executable)
            else:
                # Если запущено как Python скрипт
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            # Формируем полный путь к файлу
            file_path = os.path.join(application_path, filename)
            
            # Проверяем существование файла
            if os.path.exists(file_path):
                print(f"Файл {filename} успешно открыт")
                self.status_var.set(f"Файл {filename} открыт")
            else:
                print(f"Файл {filename} не найден в директории приложения")
                self.status_var.set(f"Файл {filename} не найден")
                messagebox.showwarning("Файл не найден", 
                                    f"Файл {filename} не найден в директории приложения.\n"
                                    f"Путь: {application_path}")
        
        except Exception as e:
            error_msg = f"Ошибка при открытии файла: {str(e)}"
            print(error_msg)
            self.status_var.set("Ошибка открытия файла")
            messagebox.showerror("Ошибка", error_msg)

        programmer = PI(self.serial_connection)
        time.sleep(2)
        # Ваш код изменения параметров будет здесь

        if(motor_number == 1):
            programmer.read_motor_1(file_path)
        elif(motor_number == 2):
            programmer.read_motor_2(file_path)
        elif(motor_number == 3):
            programmer.read_motor_3(file_path)
        elif(motor_number == 4):
            programmer.read_motor_4(file_path)
        

    def empty_function_stop_motor(self, motor_number):
        """Пустая функция останова двигателя"""
        print(f"Останов двигателя {motor_number}")
        programmer = PI(self.serial_connection)
        if(motor_number == 1):
            programmer.Start_motor_1(0)
            self.engine_1_status = 0
        elif(motor_number == 2):
            programmer.Start_motor_2(0)
            self.engine_2_status = 0
        elif(motor_number == 3):
            programmer.Start_motor_3(0) 
            self.engine_3_status = 0      
        elif(motor_number == 4):
            programmer.Start_motor_4(0)   
            self.engine_4_status = 0 
        if (self.engine_1_status == 0 and self.engine_2_status == 0 and self.engine_3_status == 0 and self.engine_4_status == 0):
            self.stop_periodic_monitoring()
            self.monitoring_status = 0

    def empty_function_start_motor(self, motor_number, thrust_value):
        """Пустая функция запуска двигателя"""
        print(f"Запуск двигателя {motor_number} с тягой {thrust_value}")
        programmer = PI(self.serial_connection)
        if(motor_number == 1):
            programmer.Start_motor_1(thrust_value)
            self.engine_1_status = 1
        elif(motor_number == 2):
            programmer.Start_motor_2(thrust_value)
            self.engine_2_status = 1
        elif(motor_number == 3):
            programmer.Start_motor_3(thrust_value) 
            self.engine_3_status = 1      
        elif(motor_number == 4):
            programmer.Start_motor_4(thrust_value) 
            self.engine_4_status = 1    
        if(self.monitoring_status == 0):
            self.start_periodic_monitoring()
            self.monitoring_status = 1
        # Ваш код запуска двигателя будет здесь
        # Используйте thrust_value для установки мощности двигателя
    
    def __del__(self):
        """Деструктор - закрываем соединение при выходе"""
        if hasattr(self, 'serial_connection') and self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

def main():
    # Создаем главное окно
    root = tk.Tk()
    
    # Создаем приложение
    app = MotorControlApp(root)
    
    # Обработка закрытия окна
    def on_closing():
        if app.is_connected:
            app.disconnect_serial()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Запускаем главный цикл
    print("Приложение запущено. Консоль активна.")
    root.mainloop()

if __name__ == "__main__":
    main()