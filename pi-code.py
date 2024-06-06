#!/usr/bin/env python3

import time
from bmp280 import BMP280
import adafruit_dht
import board
import csv
from datetime import datetime
from Adafruit_IO import Client

# Adafruit IO Setup
ADAFRUIT_IO_USERNAME = 'Rossavik'
ADAFRUIT_IO_KEY = 'hidden'
aio = Client(ADAFRUIT_IO_USERNAME, ADAFRUIT_IO_KEY)

pressoffset = 494.7447444848324
tempoffset = -1.5269793782352465
humoffset = 1.56415343915344

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

# CSV file setup
csv_file_path = '/home/local/Desktop/data_log.csv'

bus = SMBus(1)
try:
    bmp280 = BMP280(i2c_dev=bus)
    bmp280.sea_level_pressure = 1031
except Exception as e:
    print(f"Failed to initialize BMP280: {e}")

dht = adafruit_dht.DHT11(board.D18)

temperature_sum = 0
pressure_sum = 0
humidity_sum = 0
count = 0

start_time = time.time()

while True:
    try:
        temperature = bmp280.get_temperature()
        pressure = bmp280.get_pressure()
    except Exception as e:
        print(f"Failed to read from BMP280: {e}")
        temperature = None
        pressure = None

    try:
        humidity = dht.humidity
    except RuntimeError as error:
        print(error.args[0])
        humidity = None

    if temperature is not None and pressure is not None:
        temperature_sum += temperature
        pressure_sum += pressure
        count += 1

    if humidity is not None:
        humidity_sum += humidity

    if time.time() - start_time >= 30:
        avg_temperature = tempoffset + temperature_sum / count if count > 0 else None
        avg_pressure = pressoffset + pressure_sum / count if count > 0 else None
        avg_humidity = humoffset + humidity_sum / count if count > 0 else None

        # Append data to CSV
        with open(csv_file_path, 'a', newline='') as csvfile:
            data_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            data_writer.writerow([datetime.now(), avg_temperature, avg_pressure, avg_humidity])
        
        print(f"Averages over the last 30 seconds recorded at {datetime.now()}:")
        if avg_temperature and avg_pressure and avg_humidity:
            print(f"Temperature: {avg_temperature:.2f} C | Pressure: {avg_pressure:.2f} hPa | Humidity: {avg_humidity:.2f}%")
            try:
                tempfeed = aio.feeds('rbpi3bmptemp')
                humfeed = aio.feeds('rbpi3dhthum')
                pressfeed = aio.feeds('rbpi3bmppress')
                if avg_temperature is not None:
                    aio.send_data(tempfeed.key, avg_temperature)
                if avg_humidity is not None:
                    aio.send_data(humfeed.key, avg_humidity)
                if avg_pressure is not None:
                    aio.send_data(pressfeed.key, avg_pressure)
            except Exception as e:
                print(f'Failed to send data to Adafruit IO: {e}')
        else:
            print('Failed to retrieve or calculate some sensor data')

        # Reset for the next average calculation
        temperature_sum = 0
        pressure_sum = 0
        humidity_sum = 0
        count = 0
        start_time = time.time()

    time.sleep(1)


