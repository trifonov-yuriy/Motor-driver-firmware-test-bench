#include "timer.h"


void timer0_setup(void) 
{
    DDRD |= (1 << PD6);
    TCCR0A = 0;
    TCCR0B = 0;

    TCCR0A = (1 << COM0A1) | (1 << WGM01) | (1 << WGM00);
    TCCR0B |= (1 << CS02);
    // TIMSK0 |= (1 << TOIE0);
    OCR0A = 0;

}

void timer1_setup(void) 
{
    DDRB |= (1 << PB1) | (1 << PB2);
    TCCR1A = 0; 
    TCCR1B = 0;
    TCCR1A |= (1 << COM1A1) | (1 << COM1B1) | (1 << WGM10);
    TCCR1B |= (1 << CS12) | (1 << WGM12);
    // TIMSK1 |= (1 << TOIE1);

    OCR1A = 0;
    OCR1B = 0;
}

void timer2_setup(void) 
{
    DDRB |= (1 << PB3);
    TCCR2A = 0;
    TCCR2B = 0;

    TCCR2A |= (1 << COM2A1) | (1 << WGM20) | (1 << WGM21);
    TCCR2B |= (1 << CS22) | (1 << CS21);
    // TIMSK2 |= (1 << TOIE2);

    OCR2A = 0;
}