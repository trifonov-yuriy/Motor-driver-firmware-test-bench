#include "adc_.h"

volatile uint16_t adc_result = 0;
volatile uint8_t adc_result_ready_flag = 0;

void ADC_Init_With_Interrupt(void) 
{
    ADMUX = (1 << REFS0); // AVcc
    ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0) | (1 << ADIE);
    sei(); // Разрешение глобальных прерываний
    ADCSRA |= (1 << ADSC); // Первый запуск преобразования
}