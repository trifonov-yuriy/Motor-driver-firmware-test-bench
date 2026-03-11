#ifndef C2_H
#define C2_H

#include "util/delay.h"
#include "gpio.h"
#include "usart.h"
#include "isr.h"
#include "stdio.h"
#include "adc_.h"

extern volatile uint16_t c2_messagePtr;
extern volatile uint8_t c2_message[];
extern volatile uint8_t readFlag;

typedef enum  
{
  DATA_READ     = 0x00,
  DATA_WRITE    = 0x01,
  ADDRESS_READ  = 0x02,
  ADDRESS_WRITE = 0x03,
 } C2Instruction;

typedef enum  
{
  DEVICEID = 0x00,
  REVID    = 0x01,
  FPCTL    = 0x02,
  FPDAT    = 0xB4, // May be different for non EFM8 targets
  FLKEY    = 0xB7,
  DPH      = 0x83,
  DPL      = 0x82,
  PSCTL    = 0x8F,
 } C2Addresses;

typedef enum  

{
  DEVICE_ERASE = 0x03,
  BLOCK_READ   = 0x06,
  BLOCK_WRITE  = 0x07,
  PAGE_ERASE   = 0x08,
} C2Commands;

typedef enum  
{
  EFM8BB1  = 0x30,
  EFM8BB2  = 0x32,
  EFM8BB51 = 0x39,
} C2Devices;

typedef enum  
{
  ACK   = 0x00,
  INIT  = 0x01,
  RESET = 0x02,
  WRITE = 0x03,
  ERASE = 0x04,
  READ  = 0x05,
  INFO  = 0x08,
  READ_PARAMS  = 0x10,
  WRITE_PAGE   = 0x11,
  ERASE_PAGE   = 0x12,
  CHOOSE_MOTOR_1 = 0x13,
  CHOOSE_MOTOR_2 = 0x14,
  CHOOSE_MOTOR_3 = 0x15,
  CHOOSE_MOTOR_4 = 0x16,
  ENABLE_PWR     = 0x17, 
  DISABLE_PWR    = 0x18,
  ENABLE_PWR_CHECK = 0x19,
  DISABLE_PWR_CHECK = 0x1A,

  START_PWR_CHECK   = 0x1B,
  START_CURRENT_CHECK = 0x1C,

  Set_Engine_1       = 0xE1,
  Set_Engine_2       = 0xE2,
  Set_Engine_3       = 0xE3,
  Set_Engine_4       = 0xE4,

  Calibration        = 0xE0,

  Give_Current       = 0xC1,


  SHOW = 0xFF

} Actions;

typedef struct  
{
  uint8_t id;
  uint8_t revision;
} Device;



void c2_reset();
uint8_t c2_init();
void c2_deviceInfo();
void c2_writeAddress(uint8_t address);
uint8_t c2_writeSfr(uint8_t address, uint8_t data);
uint8_t c2_readBits(uint8_t length);
void c2_sendStopBit();
void c2_sendAddressReadInstruction();
void c2_sendDataReadInstruction(uint8_t byte);
void c2_sendAddressWriteInstruction();
void c2_sendDataWriteInstruction(uint8_t byte);
void c2_sendBits(uint8_t data, uint8_t length);
void c2_clockPulse();
uint8_t c2_readByte();
void c2_sendByte(uint8_t byte);
uint8_t c2_readAddress();
uint8_t c2_writeData(uint8_t data);
uint8_t c2_waitForResponse();
uint8_t c2_readData(uint8_t* response);
void c2_updateState(uint8_t data);
uint8_t c2_writeFlashBlock(uint8_t addressH, uint8_t addressL, uint8_t *data, uint8_t length);
uint8_t c2_readFlashBlock(uint16_t address, uint8_t *data, uint8_t bytes);
uint8_t c2_pollBitLow(uint8_t mask);
uint8_t c2_pollBitHigh(uint8_t mask);
uint8_t c2_getState();
void c2_resetState();
uint8_t c2_eraseDevice();
void read_blheli_parameters();
uint8_t c2_WriteParameterByAddress(uint8_t addressH, uint8_t addressL, uint8_t data, uint8_t length);
uint8_t c2_erasePage();


void c2_setup();

void c2_loop();



#endif