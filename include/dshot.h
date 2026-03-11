#include <avr/io.h>


uint16_t calculate_dshot_packet(uint16_t throttle, uint8_t telemetry);

extern volatile uint16_t engine_1;
extern volatile uint16_t engine_2; 
extern volatile uint16_t engine_3;
extern volatile uint16_t engine_4;



