#!/usr/bin/env python3

import time
import math
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

pressoffset = 326.7892752522673
tempoffset = -4.6355381523918915
humoffset = 12.364285714285714

try:
    from smbus2 import SMBus
except ImportError:
    from smbus import SMBus

# CSV file setup
csv_file_path = '/home/local/Desktop/data_log2.csv'

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

def calculate_dew_point(T, RH):
    """
    Calculate the dew point temperature using the Magnus-Tetens approximation.

    Parameters:
    T (float): the average air temperature in degrees Celsius
    RH (float): the average relative humidity in percent

    Returns:
    float: the dew point temperature in degrees Celsius
    """
    a = 17.625
    b = 243.04  # degrees Celsius

    alpha = (a * T) / (b + T) + math.log(RH / 100.0)
    dew_point = (b * alpha) / (a - alpha)
    return dew_point

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

        # Calculate dew point
        if avg_temperature is not None and avg_humidity is not None:
            avg_dew_point = calculate_dew_point(avg_temperature, avg_humidity)
        else:
            avg_dew_point = None

        # Append data to CSV
        with open(csv_file_path, 'a', newline='') as csvfile:
            data_writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            data_writer.writerow([datetime.now(), avg_temperature, avg_pressure, avg_humidity, avg_dew_point])

        # Log the averages and dew point
        print(f"Averages and Dew Point over the last 30 seconds recorded at {datetime.now()}:")
        print(f"Temperature: {avg_temperature:.2f} C | Pressure: {avg_pressure:.2f} hPa | Humidity: {avg_humidity:.2f}% | Dew Point: {avg_dew_point:.2f}°C")

        # Send to Adafruit IO
        try:
            aio.send_data('rbpi2bmptemp', avg_temperature)
            aio.send_data('rbpi2dhthum', avg_humidity)
            aio.send_data('rbpi2bmppress', avg_pressure)
            aio.send_data('rbpi2dew', avg_dew_point)
        except Exception as e:
            print(f'Failed to send data to Adafruit IO: {e}')

        # Reset for the next average calculation
        temperature_sum = 0
        pressure_sum = 0
        humidity_sum = 0
        count = 0
        start_time = time.time()

    time.sleep(1)
