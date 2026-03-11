cmake_minimum_required(VERSION 3.12)
project(avr-project C)

# Настройки для AVR
set(MCU atmega328p)
set(F_CPU 16000000UL)
#set(BOOTLOADER_OFFSET 0x800)  # ← Смещение для bootloader'а

# Настройка компилятора
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR avr)
set(CMAKE_C_COMPILER avr-gcc)
set(CMAKE_CXX_COMPILER avr-g++)
set(CMAKE_ASM_COMPILER avr-gcc)
set(CMAKE_OBJCOPY avr-objcopy)
set(CMAKE_OBJDUMP avr-objdump)
set(CMAKE_SIZE avr-size)

# Флаги компилятора
#set(CMAKE_C_FLAGS "-mmcu=${MCU} -DF_CPU=${F_CPU} -Os -Wall")
set(CMAKE_C_FLAGS "-mmcu=${MCU} -DF_CPU=${F_CPU} -Os -Wall -g -gdwarf-2")
set(CMAKE_CXX_FLAGS "-mmcu=${MCU} -DF_CPU=${F_CPU} -Os -Wall")
set(CMAKE_ASM_FLAGS "-mmcu=${MCU} -x assembler-with-cpp")


# Флаги линковщика
set(CMAKE_EXE_LINKER_FLAGS "-mmcu=${MCU} -Wl,--gc-sections -Wl,-u,vfprintf -lprintf_flt -Wl,-u,vfscanf -Wl,-u,vsprintf -Wl,-u,vsscanf -lscanf_flt -lm")
# Флаги линковки со смещением
#set(CMAKE_EXE_LINKER_FLAGS 
#    "-mmcu=${MCU} -Wl,--section-start=.text=${BOOTLOADER_OFFSET} -Wl,--gc-sections"
#)

# Исключаем тесты CMake
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)


# Пути к библиотекам
set(AVR_DIR include/AVR_library/avr)


# Исходные файлы
set(SOURCES 
    src/main.c
    src/gpio.c
    src/isr.c
    src/c2.c
    src/usart.c
    src/adc_.c
    src/timer.c
    src/dshot.c
)


# Заголовочные файлы
include_directories(
    include/
    ${AVR_DIR}/include
)

# Добавляем исполняемый файл
add_executable(${PROJECT_NAME}.elf ${SOURCES})

# Настройка формата выходного файла
set(HEX_FILE ${PROJECT_NAME}.hex)
set(EEP_FILE ${PROJECT_NAME}.eep)




# Добавьте цель для дизассемблирования
add_custom_target(disassemble
    COMMAND ${CMAKE_OBJDUMP} -S $<TARGET_FILE:${PROJECT_NAME}.elf> > ${PROJECT_NAME}.lst
    DEPENDS ${PROJECT_NAME}.elf
    COMMENT "Generating disassembly listing"
)

# Цели для генерации hex файлов
add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex -R .eeprom $<TARGET_FILE:${PROJECT_NAME}.elf> ${HEX_FILE}
    COMMAND ${CMAKE_OBJCOPY} -O ihex -j .eeprom --set-section-flags=.eeprom=alloc,load --change-section-lma .eeprom=0 $<TARGET_FILE:${PROJECT_NAME}.elf> ${EEP_FILE}
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:${PROJECT_NAME}.elf>
    COMMENT "Generating hex files"
)

# Цели для генерации hex файлов С ПРАВИЛЬНЫМ СМЕЩЕНИЕМ
#add_custom_command(TARGET ${PROJECT_NAME}.elf POST_BUILD
#    COMMAND ${CMAKE_OBJCOPY} -O ihex -R .eeprom --change-addresses=0x7800 $<TARGET_FILE:${PROJECT_NAME}.elf> ${HEX_FILE}
#    COMMAND ${CMAKE_OBJCOPY} -O ihex -j .eeprom --set-section-flags=.eeprom=alloc,load --change-section-lma .eeprom=0 $<TARGET_FILE:${PROJECT_NAME}.elf> ${EEP_FILE}
#    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:${PROJECT_NAME}.elf>
#    COMMENT "Generating hex files with bootloader offset"
#)

# Цель для прошивки
find_program(AVRDUDE avrdude)
if(AVRDUDE)
    add_custom_target(flash
        COMMAND ${AVRDUDE} -c arduino -p ${MCU} -P COM3 -b 19200 -U flash:w:${HEX_FILE}:i
        DEPENDS ${PROJECT_NAME}.elf
        COMMENT "Flashing ${HEX_FILE} to ${MCU}"
    )
endif()

if(NOT AVRDUDE)
    message( "AVRDUDE not found")
endif()


find_program(AVR_GCC avr-gcc)
if(NOT AVR_GCC)
    message(FATAL_ERROR "avr-gcc not found! Install AVR Toolchain")
endif()


# Конфигурируем CMake
# cmake -G "MinGW Makefiles" -DCMAKE_TOOLCHAIN_FILE=../avr-toolchain.cmake ..
# mingw32-make