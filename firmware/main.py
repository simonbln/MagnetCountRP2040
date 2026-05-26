from machine import Pin, I2C, ADC
import ssd1306
import neopixel
import time


try:
    pixels = neopixel.NeoPixel(Pin(16), 1)
    i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=1000000)
    oled = ssd1306.SSD1306_I2C(128, 32, i2c)

    button = Pin(3, Pin.IN, Pin.PULL_UP)
    hall = ADC(Pin(26))

    count = 0
    count_old = -1
    last_interrupt_time = 0

    def reset_counter_handler(pin):
        global count, last_interrupt_time
        current_time = time.ticks_ms()
        if (current_time - last_interrupt_time) > 200:
            count = 0
            last_interrupt_time = current_time

    button.irq(trigger=Pin.IRQ_FALLING, handler=reset_counter_handler)

    def draw_big_digit(digit, x, y):
        w, h, t = 18, 28, 3
        if digit in [0, 2, 3, 5, 6, 7, 8, 9]: oled.fill_rect(x, y, w, t, 1)
        if digit in [0, 4, 5, 6, 8, 9]:       oled.fill_rect(x, y, t, h//2, 1)
        if digit in [0, 1, 2, 3, 4, 7, 8, 9]: oled.fill_rect(x + w - t, y, t, h//2, 1)
        if digit in [2, 3, 4, 5, 6, 8, 9]:    oled.fill_rect(x, y + h//2 - t//2, w, t, 1)
        if digit in [0, 2, 6, 8]:             oled.fill_rect(x, y + h//2, t, h//2, 1)
        if digit in [0, 1, 3, 4, 5, 6, 7, 8, 9]: oled.fill_rect(x + w - t, y + h//2, t, h//2, 1)
        if digit in [0, 2, 3, 5, 6, 8, 9]:    oled.fill_rect(x, y + h - t, w, t, 1)

    def display_fixed_number(number):
        oled.fill(0)
        if number > 99999: number = 99999
        formatted_str = "{:05d}".format(number)
        for i, d in enumerate(formatted_str):
            draw_big_digit(int(d), 9 + (i * 23), 2)
        oled.show()
        
    class MagnetState:
        ABSENT = 0
        DETECTED = 1
        UNCERTAIN = 2

    THRESHOLD_HIGH = 1500
    THRESHOLD_LOW = 1000

    current_internal_state = MagnetState.ABSENT

    def get_magnet_state():
        global current_internal_state
        val = hall.read_u16()
        diff = abs(val - 32768)
        #print(diff)
        
        if diff > THRESHOLD_HIGH:
            current_internal_state = MagnetState.DETECTED
            return MagnetState.DETECTED
        elif diff < THRESHOLD_LOW:
            current_internal_state = MagnetState.ABSENT
            return MagnetState.ABSENT
        else:
            # Im Bereich dazwischen sind wir "unsicher"
            return MagnetState.UNCERTAIN


    magnet_already_counted = False


    while True:
        state = get_magnet_state()
        
        if state == MagnetState.DETECTED:
            if not magnet_already_counted:
                count += 1
                if count > 99999: count = 0
                magnet_already_counted = True
                
        elif state == MagnetState.ABSENT:
            if magnet_already_counted:
                magnet_already_counted = False

        if count != count_old:
            print(count)
            display_fixed_number(count)
            count_old = count
        else:
            time.sleep_ms(5)
except Exception as e:
    print("Fehler aufgetreten:", e)
    # Endlosschleife für das rote Blinken bei Absturz
    while True:
        pixels[0] = (255, 0, 0)  # Rot an
        pixels.write()
        time.sleep_ms(250)
        pixels[0] = (0, 0, 0)    # Aus
        pixels.write()
        time.sleep_ms(250)            
