#include <avr/io.h>
#include <avr/interrupt.h>

extern volatile uint16_t adc_result;
extern volatile uint8_t adc_result_ready_flag;




void ADC_Init_With_Interrupt(void);