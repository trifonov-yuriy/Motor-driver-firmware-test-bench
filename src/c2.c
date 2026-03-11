

#include "define.h"
#include "c2.h"
#include "avr/interrupt.h"
#include "stdlib.h"
#include "dshot.h"
#include "timer.h"

uint8_t c2_state = 0;
volatile uint8_t readFlag = 0;
volatile uint16_t c2_messagePtr;
volatile uint8_t c2_message[300];
uint8_t c2_flashBuffer[300];
volatile uint8_t c2_bytesLeft;

volatile Device device = {0};


const uint8_t _inBusy = 0x02;
const uint8_t _outReady = 0x01;

float I = 0;
float I_leak = 0;

uint8_t set_engine_flag = 0;

uint8_t calibration_flag = 0;

typedef struct 
{
    uint32_t mantissa_low:8;   // Младшие 8 бит мантиссы
    uint32_t mantissa_mid:8;   // Средние 8 бит мантиссы  
    uint32_t mantissa_high : 7;  // Старшие 7 бит мантиссы
    // uint32_t mantissa:23;
    uint32_t exponent:8;   
    uint32_t sign : 1;           // Бит знака

} float_bytes;

typedef union 
{
  float value;
  float_bytes bytes;
} float_union;

float_union U_check_pwr;
float_union I_check_pwr;

float_union U_current;
float_union I_current;

uint8_t throttle_1 = 0;
uint8_t throttle_2 = 0;
uint8_t throttle_3 = 0;
uint8_t throttle_4 = 0;

void c2_reset() 
{
  C2_CLK_OFF;
  _delay_us(30);

  C2_CLK_ON;

  _delay_us(5);
}

uint8_t c2_init() 
{
  uint8_t result = EXIT_SUCCESS;
  c2_reset();

  // Enable programming
  c2_writeAddress(FPCTL);
  result = c2_writeData(0x02);
  result = c2_writeData(0x04);
  result = c2_writeData(0x01);

  // Wait at lesat 20ms
  _delay_us(30);

  return result;
}

void c2_resetState() 
{
  c2_state = 0;
  readFlag = 0;
  c2_messagePtr = 0;
}

void c2_updateState(uint8_t data) 
{
  c2_message[c2_messagePtr] = data;
  c2_messagePtr = (c2_messagePtr + 1) ;
  /*
  switch(c2_state) 
  {
    case 0x00: 
    {
      c2_messagePtr = 0;
      c2_message[c2_messagePtr++] = data;

      c2_state = 1;
    } break;

    case 0x01: 
    {
      c2_bytesLeft = data;
      c2_message[c2_messagePtr++] = data;

      if(c2_bytesLeft == 0) 
      {
        c2_state = 3;

        break;
      }

      c2_state = 2;
    } break;

    case 0x02: 
    {
      c2_message[c2_messagePtr++] = data;
      c2_bytesLeft--;

      if(c2_bytesLeft == 0) 
      {
        c2_state = 3;
      }
    } break;
  }
    */

  //return c2_state;    
}

uint8_t c2_writeData(uint8_t data) 
{
  c2_sendDataWriteInstruction(1);
  c2_sendByte(data);
  uint16_t counter = 0;
  while (c2_readBits(1) == 0 && counter < 60000) 
  {
    counter++;
  }
  if(counter >= 60000) 
  {
    return EXIT_FAILURE;
  }
  c2_sendStopBit();
  return EXIT_SUCCESS;
}

void c2_sendByte(uint8_t byte) 
{
  c2_sendBits(byte, 8);
}

void c2_writeAddress(uint8_t address) 
{
  c2_sendAddressWriteInstruction();
  c2_sendByte(address);
  c2_sendStopBit();
}

void c2_sendDataWriteInstruction(uint8_t byte) 
{
  uint8_t data = 0x00 | (0x00 << 0) | (DATA_WRITE << 1) | ((byte - 1) << 3);
  c2_sendBits(data, 5);
}

void c2_sendAddressWriteInstruction() 
{
  uint8_t data = 0x00 | (0x00 << 0) | (ADDRESS_WRITE << 1);
  c2_sendBits(data, 3);
}

void c2_sendBits(uint8_t data, uint8_t length) 
{
  for(uint8_t i = 0; i < length; i += 1) 
  {
    if(data >> i & 0x01) 
    {
      C2_D_ON;
    } 
    else 
    {
      C2_D_OFF;
    }

    c2_clockPulse();
  }
}

void c2_clockPulse() 
{
   cli();

  // Force low for 80ns - 5000ns
  C2_CLK_OFF;
  _delay_us(2);

  // Force high for at least 120ns
  C2_CLK_ON;

  sei();
}

uint8_t c2_readBits(uint8_t length) 
{
  uint8_t mask = 0x01 << (length - 1);
  uint8_t data = 0;

  C2_D_IN;          //Настраиваем вывод data на вход
  C2_D_PULL_DOWN;   


  for (uint8_t i = 0; i < length; i += 1) 
  {
    c2_clockPulse();

    data >>= 1;
    if (C2_D_READ) 
    {
      data = data | mask;
    }
  }
  C2_D_OUT;     //Настраиваем вывод data на выход

  return data;
}


void с2_sendStopBit() 
{
  c2_sendBits(0x00, 1);
}


uint8_t с2_readAddress() 
{
  c2_sendAddressReadInstruction();
  uint8_t retval = c2_readByte();
  c2_sendStopBit();

  return retval;
}

void c2_sendAddressReadInstruction() 
{
  uint8_t data = 0x00 | (0x00 << 0) | (ADDRESS_READ << 1);
  c2_sendBits(data, 3);
}

void c2_deviceInfo() 
{
  c2_writeAddress(DEVICEID);
  c2_readData(&device.id);

  c2_writeAddress(REVID);
  c2_readData(&device.revision);
}

void c2_sendDataReadInstruction(uint8_t byte) 
{
  uint8_t data = 0x00 | (0x00 << 0) | (DATA_READ << 1) | ((byte - 1) << 3);
  c2_sendBits(data, 5);
}

uint8_t c2_readData(uint8_t* response) 
{
  c2_sendDataReadInstruction(1);
  uint8_t result = c2_waitForResponse(response);
  if(result == EXIT_SUCCESS) 
  {
    c2_sendStopBit();
    return EXIT_SUCCESS;
  }
  else 
  {
    c2_sendStopBit();
    return EXIT_FAILURE;
  }
}

uint8_t c2_waitForResponse(uint8_t* response) 
{
  uint16_t counter = 0;
  
  while(c2_readBits(1) == 0 && counter < 60000) 
  {
    counter++;
  }

  if(counter >= 60000) 
  {
    return EXIT_FAILURE;
  }

  *response = c2_readBits(8);

  return EXIT_SUCCESS;
}

uint8_t c2_writeSfr(uint8_t address, uint8_t data) 
{
//  c2_writeAddress(FPDAT);
  c2_writeAddress(address);
//  c2_writeData(BLOCK_WRITE);
//  c2_writeData(address);
  if(c2_writeData(data)) 
  {
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
  
}

uint8_t c2_getState() 
{
  return c2_state;
}



void c2_setup() 
{
    gpio_init();
    usart_init();

    usart_debug_msg("program is ready!");
   // isr_init();    
}



void c2_loop() 
{
  uint8_t crc;
  uint8_t newcrc;
  uint8_t addressL;
  uint8_t addressH;
  uint16_t address;

  uint8_t data = 0;

  uint16_t timer = 50000;

  usart_debug_msg("start loop!");
  c2_resetState();

  while(1) 
  {
    if(timer) 
    {
      timer--;
      if(timer == 0) 
      {
       
        if(OCR0A > throttle_1) 
        {
          OCR0A--;
          // sprintf(debugStr, "OCR0A:%d", OCR0A);
          // usart_transmit_string(debugStr);
        }
        else if(OCR0A < throttle_1) 
        {
          OCR0A++;
          // sprintf(debugStr, "OCR0A:%d", OCR0A);
          // usart_transmit_string(debugStr);
        }

        if(OCR1A > throttle_2) 
        {
          OCR1A--;
          // sprintf(debugStr, "OCR1A:%d", OCR1A);
          // usart_transmit_string(debugStr);
        }
        else if(OCR1A < throttle_2) 
        {
          OCR1A++;
          // sprintf(debugStr, "OCR1A:%d", OCR1A);
          // usart_transmit_string(debugStr);
        }
        
        if(OCR1B > throttle_3) 
        {
          OCR1B--;
          // sprintf(debugStr, "OCR1B:%d", OCR1B);
          // usart_transmit_string(debugStr);
        }
        else if(OCR1B < throttle_3) 
        {
          OCR1B++;
          // sprintf(debugStr, "OCR1B:%d", OCR1B);
          // usart_transmit_string(debugStr);
        }
        
        if(OCR2A > throttle_4) 
        {
          OCR2A--;
          // sprintf(debugStr, "OCR2A:%d", OCR2A);
          // usart_transmit_string(debugStr);
        }
        else if(OCR2A < throttle_4) 
        {
          OCR2A++;
          // sprintf(debugStr, "OCR2A:%d", OCR2A);
          // usart_transmit_string(debugStr);
        }        

        timer = 50000;

      }
    }
    if(readFlag) 
    {
        {
            switch(c2_message[0]) 
            {
                case CHOOSE_MOTOR_1: 
                {
                  ESC_1;
                  usart_debug_msg("CHOOSE_MOTOR_1");
                  usart_data_msg(0x80);
                  c2_resetState();
                } break;

                case CHOOSE_MOTOR_2: 
                {
                  ESC_2;
                  usart_debug_msg("CHOOSE_MOTOR_2");
                  usart_data_msg(0x80);
                  c2_resetState();
                } break;

                case CHOOSE_MOTOR_3:
                {
                  ESC_3;
                  usart_debug_msg("CHOOSE_MOTOR_3");
                  usart_data_msg(0x80);
                  c2_resetState();
                } break;
                
                case CHOOSE_MOTOR_4: 
                {
                  ESC_4;
                  usart_debug_msg("CHOOSE_MOTOR_4");
                  usart_data_msg(0x80);
                  c2_resetState();
                } break;

                case ENABLE_PWR_CHECK: 
                {
                  POWER_CHECK_ON;
                  usart_debug_msg("ENABLE_PWR_CHECK");
                  usart_data_msg(0x80);
                  c2_resetState();
                } break;                

                case DISABLE_PWR_CHECK: 
                {
                  calibration_flag = 0;
                  POWER_CHECK_OFF;
                  usart_debug_msg("DISABLE_PWR_CHECK"); 
                  usart_data_msg(0x80);
                  c2_resetState();
                } break;     

                case ENABLE_PWR: 
                {
                  POWER_ON;
                  usart_debug_msg("ENABLE_PWR");
                  usart_data_msg(0x80);
                  c2_resetState();
                } break;                

                case DISABLE_PWR: 
                {
                  POWER_OFF;
                  calibration_flag = 0;
                  usart_debug_msg("DISABLE_PWR");
                  usart_data_msg(0x80);
                  c2_resetState();
                } break;      
                
                case START_CURRENT_CHECK: 
                {
                 
                  CURRENT_CHECK_ADC;
                  usart_debug_msg("START_CURRENT_CHECK");
                  usart_data_msg(0x80);
                  U_current.value = 0;
                  I_current.value = 0;

                  ADC_START;
                  while(adc_result_ready_flag == 0);
                  adc_result_ready_flag = 0;
                  U_current.value = (5 * adc_result) / 1023.0f;
                  I_current.value = (10 * U_current.value / 0.015f);
                  sprintf(debugStr, "I=%.2f", I_current.value);
                  usart_debug_msg(debugStr);
                  usart_data_msg(U_current.bytes.sign);
                  usart_data_msg(U_current.bytes.exponent);
                  usart_data_msg(U_current.bytes.mantissa_high);
                  usart_data_msg(U_current.bytes.mantissa_mid);
                  usart_data_msg(U_current.bytes.mantissa_low);                  
                  usart_data_msg(I_current.bytes.sign);
                  usart_data_msg(I_current.bytes.exponent);
                  usart_data_msg(I_current.bytes.mantissa_high);
                  usart_data_msg(I_current.bytes.mantissa_mid);
                  usart_data_msg(I_current.bytes.mantissa_low);                  

                  c2_resetState();
                } break;    
                
                case START_PWR_CHECK: 
                {
                  POWER_CHECK_ADC;
                  usart_debug_msg("START_PWR_CHECK"); 
                  usart_data_msg(0x80);
                  U_check_pwr.value = 0;
                  I_check_pwr.value = 0;

                  ADC_START;
                  while(adc_result_ready_flag == 0);
                  adc_result_ready_flag = 0;
                  U_check_pwr.value = (5 * adc_result) / 1023.0f;
                  U_check_pwr.value = U_check_pwr.value * 9.2f;
                  I_check_pwr.value = ((24 - U_check_pwr.value) / 240.0f) - (U_check_pwr.value / 92000.0f);
                  sprintf(debugStr, "I=%.2f", I_check_pwr.value);
                  usart_debug_msg(debugStr);
                  usart_data_msg(U_check_pwr.bytes.sign);
                  usart_data_msg(U_check_pwr.bytes.exponent);
                  usart_data_msg(U_check_pwr.bytes.mantissa_high);
                  usart_data_msg(U_check_pwr.bytes.mantissa_mid);
                  usart_data_msg(U_check_pwr.bytes.mantissa_low);                  
                  usart_data_msg(I_check_pwr.bytes.sign);
                  usart_data_msg(I_check_pwr.bytes.exponent);
                  usart_data_msg(I_check_pwr.bytes.mantissa_high);
                  usart_data_msg(I_check_pwr.bytes.mantissa_mid);
                  usart_data_msg(I_check_pwr.bytes.mantissa_low);
                          
                
                  c2_resetState();
                } break;                    

                case ACK: 
                {
                  usart_debug_msg("ACK");
                  usart_data_msg(0x80);
                  c2_resetState();
                } break;

                case INIT: 
                {
                    usart_debug_msg("INIT");  
                    C2_D_OUT;
                    C2_CLK_OUT;
                    if(c2_init()) 
                    {
                        usart_debug_msg("INIT FAILED!");
                        usart_data_msg(0x43);
                        c2_resetState();
                                     
                    }
                    else 
                    {
                      c2_deviceInfo();
                      sprintf(debugStr, "c2_device.id: %d", device.id);
                      usart_debug_msg(debugStr);   
                      sprintf(debugStr, "c2_device.revision: %d", device.revision);
                      usart_debug_msg(debugStr);                       
                      switch(device.id) 
                      {
                          case EFM8BB1:
                          case EFM8BB2: 
                          {
                              c2_writeSfr(0xFF, 0x80);
                              _delay_us(5);
                              c2_writeSfr(0xEF, 0x02);
                          } break;
                      }

                      usart_data_msg(0x81);

                      c2_resetState();
                    }
              } break;

                case RESET: 
                {
                    usart_debug_msg("RESET");  
                    c2_reset();
                    c2_resetState();

                    usart_data_msg(0x82);
                } break;

                case WRITE: 
                {
                    usart_debug_msg("WRITE"); 
                    while(c2_messagePtr <= (c2_message[1] - 1));
                    addressH = c2_message[4];
                    addressL = c2_message[5];
                    crc = c2_message[6];
                    uint16_t value = (c2_message[5] + c2_message[4]) & 0xff;
                    newcrc = value;
                    
                    
                    for(uint16_t i = 0; i < c2_message[2]; i+= 1) 
                    {
                      c2_flashBuffer[i] = c2_message[i+7];
                    }

                    for(uint8_t i = 0; i < c2_message[2]; i += 1) 
                    {
                      newcrc += c2_flashBuffer[i];
                    }
                    sprintf(debugStr, "crc = %d, newcrc = %d", crc, newcrc);
                    usart_debug_msg(debugStr);
                    if(crc != newcrc) 
                    {
                        usart_debug_msg("FAILED! crc != newcrc");
                        usart_data_msg(0x43);
                        c2_resetState();
                        break;
                    }

                    uint8_t ch = c2_message[2];                   
                    if(c2_writeFlashBlock(addressH, addressL, c2_flashBuffer, ch)) 
                    {
                      usart_debug_msg("writeFlashBlock FAILED!");
                      usart_data_msg(0x44);
                      c2_resetState();
                      break;                        
                    }
                    usart_debug_msg("WRITE Block Success");  
                    usart_data_msg(0x83);

                    c2_resetState();
                } break;

                case ERASE_PAGE:
                {
                  usart_debug_msg("ERASE_PAGE"); 
                  if(c2_erasePage()) 
                  {
                    usart_debug_msg("erasePage FAILED!");
                    usart_data_msg(0x44);
                    c2_resetState();
                    break;        
                  }
                  else 
                  {
                    usart_debug_msg("erasePage SUCCESS");
                    usart_data_msg(0x83);

                    c2_resetState();     
                                   
                  }                  
                } break;

                case WRITE_PAGE: 
                {
                  usart_debug_msg("WRITE_PAGE"); 
                  while(c2_messagePtr <= (c2_message[1] - 1));
                  addressH = c2_message[4];
                  addressL = c2_message[5];
                  uint16_t value = (c2_message[5] + c2_message[4]) & 0xff;
                  crc = c2_message[6];
                  newcrc = value;

                  for(uint16_t i = 0; i < c2_message[2]; i+= 1) 
                  {
                    c2_flashBuffer[i] = c2_message[i+7];
                  }

                  for(uint8_t i = 0; i < c2_message[2]; i += 1) 
                  {
                    newcrc += c2_flashBuffer[i];
                  }
                  sprintf(debugStr, "crc = %d, newcrc = %d", crc, newcrc);
                  usart_debug_msg(debugStr);
                  if(crc != newcrc) 
                  {
                      usart_debug_msg("FAILED! crc != newcrc");
                      usart_data_msg(0x43);
                      c2_resetState();
                      break;
                  }

                  uint8_t ch = c2_message[2];
                  
                  if(c2_writeFlashBlock(addressH, addressL, c2_flashBuffer, ch)) 
                  {
                    usart_debug_msg("WriteParameterByAddress FAILED!");
                    usart_data_msg(0x44);
                    c2_resetState();
                    break;                        
                  }
                  usart_debug_msg("WriteParameterByAddress Success");
                  usart_data_msg(0x83);

                  c2_resetState();
              
                } break;

                case ERASE: 
                {
                  usart_debug_msg("ERASE"); 
                  if(c2_eraseDevice()) 
                  {
                      usart_debug_msg("eraise FAILED!");
                      c2_resetState();
                  }
                  else 
                  {
                    usart_debug_msg("eraise SUCCESS");
                    c2_resetState();

                    usart_data_msg(0x84);
                  }
                } break;

                case READ: 
                {
                  usart_debug_msg("READ");
                  uint8_t byteCount = c2_message[2];
                  addressH = c2_message[4];
                  addressL = c2_message[5];                  
                  unsigned long addressPart1 = ((unsigned long)(c2_message[3])) << 16;
                  unsigned long addressPart2 = ((unsigned long)(c2_message[4])) << 8;
                  unsigned long addressPart3 = ((unsigned long)(c2_message[5])) << 0;

                  address = addressPart1 | addressPart2 | addressPart3;
                  if(c2_readFlashBlock(address, c2_flashBuffer, byteCount)) 
                  {
                    usart_debug_msg("readFlashBlock FAILED!");
                    usart_transmit_uint8_t(0x48);
                    usart_transmit_uint8_t(0x48);
                    c2_resetState();
                  }
                  else 
                  {
                    sprintf(debugStr, "readFlashBlock SUCCESS. Addr = %d", address);
                    usart_debug_msg(debugStr);
                  

                    usart_transmit_uint8_t(0xc0);
                    usart_transmit_uint8_t(0xc0);
                    for(uint8_t i = 0; i < byteCount; i++) 
                    {
                      usart_transmit_uint8_t(c2_flashBuffer[i]);
                    }
                    usart_transmit_string("\r\n");

                  
                    c2_resetState();

                    usart_data_msg(0x85);
                }
                } break;

                /*
                case 0x06: {
                c2_writeAddress(_message[3]);
                c2_writeData(_message[4]);
                c2_resetState();

                Serial.write(0x86);
                } break;

                case 0x07: {
                c2_writeAddress(_message[3]);
                data = c2_readData();
                resetState();

                Serial.write(data);
                Serial.write(0x87);
                } break;
                */

                case INFO: 
                {
                  usart_debug_msg("INFO");  
                  sprintf(debugStr, "device.id = %d", device.id);
                  usart_debug_msg(debugStr);
                  sprintf(debugStr, "device.revision = %d", device.revision);
                  usart_debug_msg(debugStr);   
                  usart_data_msg(0x88);
                  c2_resetState();
                } break;

                case READ_PARAMS:
                {
                  usart_debug_msg("READ_PARAMS");  
                  read_blheli_parameters();
                  c2_resetState();
                } break;

                case Set_Engine_1: 
                {
                  usart_debug_msg("Set_Engine_1");
                  throttle_1 = c2_message[1];
                  throttle_1 = ((throttle_1 * 63) / 100) + 62;
                  sprintf(debugStr, "throttle=%d", throttle_1);
                  usart_debug_msg(debugStr);
                      
                  // OCR0A = throttle_1;
                  

                  c2_resetState();

                } break;

                case Set_Engine_2: 
                {
                  usart_debug_msg("Set_Engine_2");
                  throttle_2 = c2_message[1];
                  throttle_2 = ((throttle_2 * 63) / 100) + 62;
                  sprintf(debugStr, "throttle=%d", throttle_2);
                  usart_debug_msg(debugStr);

                  // OCR1A = throttle_2;

                  c2_resetState();
                } break;

                case Set_Engine_3: 
                {
                  usart_debug_msg("Set_Engine_3");
                  throttle_3 = c2_message[1];
                  throttle_3 = ((throttle_3 * 63) / 100) + 62;
                  sprintf(debugStr, "throttle=%d", throttle_3);
                  usart_debug_msg(debugStr);

                  // OCR1B = throttle_3;

                  c2_resetState();
                } break;

                case Set_Engine_4: 
                {
                  usart_debug_msg("Set_Engine_4");
                  throttle_4 = c2_message[1];
                  throttle_4 = ((throttle_4 * 63) / 100) + 62;
                  sprintf(debugStr, "throttle=%d", throttle_4);
                  usart_debug_msg(debugStr);

                  // OCR2A = throttle_4;

                  c2_resetState();
                } break;

                case Calibration:
                {
                  
                  usart_debug_msg("Calibration");
                  if(!calibration_flag) 
                  {
                    calibration_flag = 1;    
                    uint8_t throttle = ((100 * 63) / 100) + 62;
                    sprintf(debugStr, "throttle=%d", throttle);
                    throttle_1 = throttle;
                    throttle_2 = throttle;
                    throttle_3 = throttle;
                    throttle_4 = throttle;
                    usart_debug_msg(debugStr);
                    OCR0A = throttle;
                    OCR1A = throttle;
                    OCR1B = throttle;
                    OCR2A = throttle;

                    _delay_ms(1000);
                    POWER_ON;
                    _delay_ms(5000);

                    throttle = ((0 * 63) / 100) + 62;
                    sprintf(debugStr, "throttle=%d", throttle);
                    usart_debug_msg(debugStr);
                    throttle_1 = throttle;
                    throttle_2 = throttle;
                    throttle_3 = throttle;
                    throttle_4 = throttle;
                    OCR0A = throttle;
                    OCR1A = throttle;
                    OCR1B = throttle;
                    OCR2A = throttle;
                    _delay_ms(5000);   
                  }   

                  usart_debug_msg("Calibration Done");       
                  usart_data_msg(0x80);

                  c2_resetState();
                  
                } break;


                case Give_Current:
                {
                  CURRENT_CHECK_ADC;
                  U_current.value = 0;
                  I_current.value = 0;
                  ADC_START;
                  while(adc_result_ready_flag == 0);
                  adc_result_ready_flag = 0;
                  U_current.value = (5 * adc_result) / 1023.0f;
                  I_current.value = (10 * U_current.value / 0.15f);              
                  usart_transmit_uint8_t((uint8_t) I_current.bytes.sign);
                  usart_transmit_uint8_t((uint8_t) I_current.bytes.exponent);
                  usart_transmit_uint8_t((uint8_t) I_current.bytes.mantissa_high);
                  usart_transmit_uint8_t((uint8_t) I_current.bytes.mantissa_mid);
                  usart_transmit_uint8_t((uint8_t) I_current.bytes.mantissa_low);                  
                  c2_resetState();                  
                }



                case SHOW:
                {
                  
                  sprintf(debugStr, "%X, %X, %X, %X, %X", U_check_pwr.bytes.sign, U_check_pwr.bytes.exponent, U_check_pwr.bytes.mantissa_high, U_check_pwr.bytes.mantissa_mid, U_check_pwr.bytes.mantissa_low);
                  // sprintf(debugStr, "%X, %X, %X,", show.bytes.sign, show.bytes.exponent, show.bytes.mantissa);
                  usart_transmit_string(debugStr);
                  c2_resetState();
                } break;

                default: 
                {
                  usart_debug_msg("DEFAULT");  
                  c2_resetState();
                } break;
            }
        }


    }
  }
}

uint8_t c2_eraseDevice() 
{
  c2_writeAddress(FPDAT);
  c2_writeData(DEVICE_ERASE);

  c2_pollBitLow(_inBusy);
  c2_pollBitHigh(_outReady);

  uint8_t value = 0;
  
  if(c2_readData(&value)) 
  {
    return EXIT_FAILURE;
  }

  usart_debug_msg(debugStr);
  if(value != 0x0D) 
  {
    return EXIT_FAILURE;
  }

  c2_writeData(0xDE);
  c2_pollBitLow(_inBusy);

  c2_writeData(0xAD);
  c2_pollBitLow(_inBusy);

  c2_writeData(0xA5);
  c2_pollBitLow(_inBusy);
  c2_pollBitHigh(_outReady);

  if(c2_readData(&value)) 
  {
    return EXIT_FAILURE;
  }

  if(value != 0x0D) 
  {
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}

uint8_t c2_readFlashBlock(uint16_t address, uint8_t *data, uint8_t bytes) 
{
  c2_writeAddress(FPDAT);
  
  if(c2_writeData(BLOCK_READ)) 
  {
    return EXIT_FAILURE;
  }
  
 
  if(c2_pollBitLow(_inBusy)) 
  {
    return EXIT_FAILURE;
  }

  if(c2_pollBitHigh(_outReady)) 
  {
    return EXIT_FAILURE;
  }

  uint8_t value;
  
  if(c2_readData(&value)) 
  {
    return EXIT_FAILURE;
  }
  if(value != 0x0D) 
  {
    return EXIT_FAILURE;
  }
  
  // Write high byte of addres
  if(c2_writeData(address >> 8)) 
  {
    return EXIT_FAILURE;
  }
  if(c2_pollBitLow(_inBusy)) 
  {
    return EXIT_FAILURE;
  }

  
  // Write low byte of address
  if(c2_writeData(address & 0xFF)) 
  {
    return EXIT_FAILURE;
  }
 
  if(c2_pollBitLow(_inBusy)) 
  {
    return EXIT_FAILURE;
  }
  
  if(c2_writeData(bytes)) 
  {
    return EXIT_FAILURE;
  }

  if(c2_pollBitLow(_inBusy)) 
  {
    return EXIT_FAILURE;
  }

  if(c2_pollBitHigh(_outReady)) 
  {
    return EXIT_FAILURE;
  }

  if (c2_readData(&value)) 
  {
    return EXIT_FAILURE;
  }
   uint8_t j = 0;
  for(uint8_t i = 0; i < bytes; i += 1) 
  {

    if(c2_pollBitHigh(_outReady)) 
    {
      return EXIT_FAILURE;
    }

    if(c2_readData(&data[i])) 
    {
        
      return EXIT_FAILURE;
    }
  }
  
  return EXIT_SUCCESS;
}

void c2_sendStopBit() 
{
  c2_sendBits(0x00, 1);
}

uint8_t c2_readAddress() 
{
  c2_sendAddressReadInstruction();
  uint8_t retval = c2_readByte();
  c2_sendStopBit();

  return retval;
}

uint8_t c2_readByte() 
{
  return c2_readBits(8);
}

uint8_t c2_pollBitHigh(uint8_t mask) 
{
  uint8_t retval;
  uint16_t counter = 0;
  do 
  {
    retval = c2_readAddress();
    counter++;
  } while ((retval & mask) == 0 && counter < 6000);

  if(counter >= 6000) 
  {
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}

uint8_t c2_pollBitLow(uint8_t mask) 
{
  uint8_t retval;
  uint16_t counter = 0;
  do 
  {
    retval = c2_readAddress();
    counter++;
  } while (retval & mask && counter < 6000);

  if(counter >= 6000) 
  {
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}

uint8_t c2_erasePage() 
{
  sprintf(debugStr, "erasePage");
  usart_debug_msg(debugStr); 
  uint8_t data = 0;

  c2_writeAddress(FPDAT);
  c2_writeData(PAGE_ERASE);

  c2_pollBitLow(_inBusy);
  c2_pollBitHigh(_outReady);

  uint8_t value = 0;
  
  if(c2_readData(&value)) 
  {
    return EXIT_FAILURE;
  }

  if(value != 0x0D) 
  {
    return EXIT_FAILURE;
  }

  c2_writeData(13);
  c2_pollBitLow(_inBusy);
  c2_pollBitHigh(_outReady);

  if(c2_readData(&value)) 
  {
    return EXIT_FAILURE;
  }

  if(value != 0x0D) 
  {
    return EXIT_FAILURE;
  }

  c2_writeData(0x00);
  c2_pollBitLow(_inBusy);
  c2_pollBitHigh(_outReady);

  if(c2_readData(&value)) 
  {
    return EXIT_FAILURE;
  }

  if(value != 0x0D) 
  {
    return EXIT_FAILURE;
  }

  
  return EXIT_SUCCESS;
}

uint8_t c2_WriteParameterByAddress(uint8_t addressH, uint8_t addressL, uint8_t data, uint8_t length) 
{
  sprintf(debugStr, "writeParameterByAddress. AddrH = %d; AddrL = %d", addressH, addressL);
  usart_debug_msg(debugStr);   

 
}

uint8_t c2_writeFlashBlock(uint8_t addressH, uint8_t addressL, uint8_t *data, uint8_t length) 
{
  sprintf(debugStr, "writeFlashBlock. AddrH = %d; AddrL = %d", addressH, addressL);
  usart_debug_msg(debugStr);   
  c2_writeAddress(FPDAT);
  if(c2_writeData(BLOCK_WRITE)) 
  {
    return EXIT_FAILURE;
  }

  if( c2_pollBitLow(_inBusy)) 
  {
      return EXIT_FAILURE;
  }
 
  if(c2_pollBitHigh(_outReady)) 
  {
    return EXIT_FAILURE;
  }

  uint8_t value;
  if(c2_readData(&value)) 
  {
    return EXIT_FAILURE;
  }
  if(value != 0x0D) 
  {
    return EXIT_FAILURE;
  }

  // Write high byte of address

  if(c2_writeData(addressH)) 
  {
    return EXIT_FAILURE;
  }

  if (c2_pollBitLow(_inBusy)) 
  {
    return EXIT_FAILURE;
  }

  // Write low byte of address
  if(c2_writeData(addressL)) 
  {
    return EXIT_FAILURE;
  }
  if(c2_pollBitLow(_inBusy)) 
  {
    return EXIT_FAILURE;
  }

  if(c2_writeData(length)) 
  {
    return EXIT_FAILURE;
  }

  if(c2_pollBitLow(_inBusy)) 
  {
    return EXIT_FAILURE;
  }

  for(uint8_t i = 0; i < length; i += 1) 
  {
    if(c2_writeData(data[i])) 
    {
      return EXIT_FAILURE;
    }
    if(c2_pollBitLow(_inBusy)) 
    {
      return EXIT_FAILURE;
    }
  }
  if(c2_pollBitHigh(_outReady)) 
  {
    return EXIT_FAILURE;
  }

  if(c2_readData(&value)) 
  {
    return EXIT_FAILURE;
  }
  if(value != 0x0D) 
  {
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}


void read_blheli_parameters() 
{
    uint8_t params[13];
    
    // Адреса параметров
    uint8_t param_addresses[] = {
        0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 
        0x87, 0x88, 0x89, 0x8A, 0x8B, 0x8C
    };
    
    const char *param_names[] = {
        "Startup Power", "Temp Protection", "Low RPM Protect",
        "Motor Direction", "Demag Comp", "Motor Timing",
        "PPM Min Throttle", "PPM Max Throttle", "PPM Center Throttle",
        "Brake On Stop", "Beep Volume", "Beacon Volume", "Beacon Delay"
    };
    
    usart_debug_msg("Reading BLHeli parameters...");
    
    for (uint8_t i = 0; i < 13; i++) 
    {
        c2_writeAddress(param_addresses[i]);
        if (c2_readData(&params[i]) == EXIT_SUCCESS) 
        {
            sprintf(debugStr, "%s: 0x%02X (%d)", param_names[i], params[i], params[i]);
            usart_debug_msg(debugStr);
        } 
        else 
        {
            sprintf(debugStr, "Failed to read %s", param_names[i]);
            usart_debug_msg(debugStr);
        }
        _delay_ms(10);
    }
}