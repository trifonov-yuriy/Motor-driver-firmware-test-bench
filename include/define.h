#define __AVR_ATmega328P__
#define __UINT8_TYPE__
#define __UINT16_TYPE__
#define __UINT32_TYPE__

#define F_CPU               16000000UL
#define USART_BAUD_RATE     19200

#define F_CPU_              160000
#define USART_BAUD_RATE_    192


#define C2_D                    PD2
#define C2_CLK                  PD3

#define A_PIN                   PD4               
#define B_PIN                   PD5

#define POWER_CHECK_PIN         PD7
#define POWER_PIN               PC1

#define CURRENT_PIN             PC0

#define SHORT_CIRCUIT_CHECK_PIN     PC3

#define POWER_CHECK_ADC         (ADMUX = (ADMUX & 0xf8) | 3)
#define CURRENT_CHECK_ADC       (ADMUX = (ADMUX & 0xf8))

#define ADC_START               ADCSRA |= (1 << ADSC);

#define ESC_1                    {PORTD &= ~(1 << A_PIN); PORTD &= ~(1 << B_PIN);}    //A=0 B=0   
#define ESC_2                    {PORTD |= (1 << A_PIN); PORTD &= ~(1 << B_PIN);}    //A=1 B=0
#define ESC_3                    {PORTD &= ~(1 << A_PIN); PORTD |= (1 << B_PIN);}    //A=0 B=1
#define ESC_4                    {PORTD |= (1 << A_PIN); PORTD |= (1 << B_PIN);}    //A=0 B=1

#define POWER_CHECK_ON          (PORTD |= (1 << POWER_CHECK_PIN))
#define POWER_CHECK_OFF         (PORTD &= ~(1 << POWER_CHECK_PIN))

#define POWER_ON                (PORTC |= (1 << POWER_PIN))
#define POWER_OFF               (PORTC &= ~(1 << POWER_PIN))

#define C2_D_IN                 DDRD &= ~(1 << PD2)
#define C2_CLK_IN               DDRD &= ~(1 << PD3)
#define C2_D_OUT                DDRD |= (1 << PD2)
#define C2_CLK_OUT              DDRD |= (1 << PD3)

#define C2_D_READ               PIND & (1 << PD2)


#define C2_D_PULL_DOWN          PORTD &= ~(1 << PD2)


#define C2_D_ON                 PORTD |= (1 << PD2)
#define C2_CLK_ON               PORTD |= (1 << PD3)

#define C2_D_OFF                PORTD &= ~(1 << PD2)
#define C2_CLK_OFF              PORTD &= ~(1 << PD3)

#define c2_message_BUFFER       300

#define PARAM_STARTUP_POWER      0x80
#define PARAM_TEMP_PROTECTION    0x81
#define PARAM_LOW_RPM_PROTECT    0x82
#define PARAM_MOTOR_DIRECTION    0x83
#define PARAM_DEMAG_COMP         0x84
#define PARAM_MOTOR_TIMING       0x85
#define PARAM_PPM_MIN_THROTTLE   0x86
#define PARAM_PPM_MAX_THROTTLE   0x87
#define PARAM_PPM_CENTER_THROTTLE 0x88
#define PARAM_BRAKE_ON_STOP      0x89
#define PARAM_BEEP_VOLUME        0x8A
#define PARAM_BEACON_VOLUME      0x8B
#define PARAM_BEACON_DELAY       0x8C
