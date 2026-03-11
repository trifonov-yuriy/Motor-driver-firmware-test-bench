#include "usart.h"
#include "stdlib.h"

volatile char debugStr[100];

void usart_init() 
{
    
    uint32_t ubbr = (F_CPU_ / (16 * USART_BAUD_RATE_)) - 1;


    UBRR0L = 0;
    UBRR0H = 0;
    UCSR0A = 0;
    UCSR0B = 0;
    UCSR0C = 0;

    UBRR0L = ubbr & 0xff;
    UBRR0H = (ubbr & (0xff00)) >> 8;

    UCSR0A = 0;
    sei();
    UCSR0B |= (1 << TXEN0) | (1 << RXEN0) | (1 << RXCIE0);
    UCSR0C |= (1 << UCSZ01) | (1 << UCSZ00);    //8 bit data
    UCSR0B &= ~(1 << UCSZ02);                   //8 bit data

}

uint8_t usart_available() 
{
    return (UCSR0A & (1 << RXC0));
}

// Передача одного символа
void usart_transmit_char(char data) 
{
    // Ожидание освобождения буфера передачи
    while (!(UCSR0A & (1 << UDRE0)));
    
    // Запись данных в буфер, отправка
    UDR0 = data;
}

// Передача одного байта                                                                                                        
void usart_transmit_uint8_t(uint8_t data) 
{
    // Ожидание освобождения буфера передачи
    while (!(UCSR0A & (1 << UDRE0)));
    
    // Запись данных в буфер, отправка
    UDR0 = data;
}

void usart_transmit_int(int data) 
{
    // Ожидание освобождения буфера передачи
    while (!(UCSR0A & (1 << UDRE0)));
    
    // Запись данных в буфер, отправка
    UDR0 = data;
}



// Передача строки
void usart_transmit_string(char* str) 
{
    while (*str) 
    {
        usart_transmit_char(*str++);
    }
    usart_transmit_char('\r');
    usart_transmit_char('\n');
}

// Передача строки
void usart_debug_msg(const char* str) 
{
    usart_transmit_uint8_t(0xDE); 
    usart_transmit_uint8_t(0xDE); 

    sprintf(debugStr, str);
    
    usart_transmit_string(debugStr);
}

void usart_data_msg(uint8_t data) 
{
    usart_transmit_uint8_t(0xC0); 
    usart_transmit_uint8_t(0xC0); 
    usart_transmit_uint8_t(data);
}

uint8_t usart_readByte() 
{
    uint8_t received_data = UDR0;
    return received_data;
}