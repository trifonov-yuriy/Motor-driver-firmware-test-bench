#include "dshot.h"

volatile uint16_t engine_1 = 0;
volatile uint16_t engine_2 = 0; 
volatile uint16_t engine_3 = 0;
volatile uint16_t engine_4 = 0;



uint16_t calculate_dshot_packet(uint16_t throttle, uint8_t telemetry) 
{
    // Проверка диапазона throttle
    if (throttle > 2047) throttle = 2047;
    
    // Формируем пакет: 11 бит throttle + 1 бит telemetry
    uint16_t packet = (throttle << 1) | (telemetry & 0x01);
    
    // Вычисляем контрольную сумму (4 бита)
    // XOR всех нибблов (4-битных групп) пакета
    uint8_t crc = (packet ^ (packet >> 4) ^ (packet >> 8)) & 0x0F;
    
    // Инвертируем контрольную сумму
    crc = (~crc) & 0x0F;
    
    // Формируем итоговый 16-битный пакет
    uint16_t dshot_packet = (packet << 4) | crc;
    
    return dshot_packet;
}
