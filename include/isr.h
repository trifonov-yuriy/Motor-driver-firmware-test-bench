#include "define.h"
#include "avr/io.h"
#include "avr/interrupt.h"

#include "c2.h"
#include "adc_.h"
#include "timer.h"

void isr_init();
ISR(USART_RX_vect);
ISR(ADC_vect);


