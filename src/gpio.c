
#include "gpio.h"




 void gpio_init() 
 {
   DDRD |= /*(1 << C2_D) | (1 << C2_CLK) |*/ (1 << B_PIN) | (1 << POWER_CHECK_PIN) | (1 << PD6); 
   DDRD |= (1 << A_PIN);

   DDRC |= (1 << POWER_PIN);

   DDRB |= (1 << PB1) | (1 << PB2) | (1 << PB3);


 }