#include "isr.h"

void isr_init() 
{
    sei();
}

ISR(USART_RX_vect) 
{
  // Чтение принятых данных
    uint8_t received_data = UDR0;

    c2_message[c2_messagePtr] = received_data;

    c2_messagePtr  = (c2_messagePtr + 1) % c2_message_BUFFER;

    readFlag = 1;
}


ISR(ADC_vect) 
{
    adc_result = ADC; // Чтение результата в обработчике прерывания
    adc_result_ready_flag = 1;
    //ADCSRA |= (1 << ADSC); // Автоматический запуск следующего преобразования
}

ISR(TIMER0_OVF_vect) 
{
    TCNT0 = 128;
}

ISR(TIMER1_OVF_vect) 
{
    TCNT1L = 128;
    TCNT1H = 0;
}

ISR(TIMER2_OVF_vect) 
{
    TCNT2 = 128;
}