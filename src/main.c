#include "define.h"

#include "c2.h"
#include "timer.h"




int main(void) 
{
    /*
    DDRB |= (1 << PB5);
    usart_init();


    while(1) 
    {
        PORTB |= (1 << PB5);
         _delay_ms(100);
        if(usart_available()) 
        {
            if(usart_readByte() == (uint8_t) 'H') 
            {
                usart_transmit_string("Hello World!\r\n");
            }
        }
        PORTB &= ~(1 << PB5);
        _delay_ms(100);
    }


    */

    gpio_init();
    timer0_setup();
    timer1_setup();
    timer2_setup();

    
    ADC_Init_With_Interrupt();
    
    
    ESC_1;
    C2_D_IN;
    C2_CLK_IN;


    c2_setup();

    //CURRENT_CHECK_ADC;

    c2_loop();

    
    return 0;
}