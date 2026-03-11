#include "define.h"
#include "avr/io.h"
#include "avr/interrupt.h"
#include "util/delay.h"

#define usart_transmit(x) _Generic((x), \
    char: usart_transmit_char, \
    uint8_t: usart_transmit_uint8_t, \
    int: usart_transmit_int \
)(x)


extern volatile char debugStr[];

void usart_init();

uint8_t usart_available();

uint8_t usart_readByte();

void usart_transmit_char(char data);

void usart_transmit_uint8_t(uint8_t data);

void usart_transmit_int(int data);

void usart_transmit_string(char* str);

char usart_receive(void);

void usart_debug_msg(const char* str);

void usart_data_msg(uint8_t data);