import requests
import numpy as np
import json
import pandas as pd

from os import path, getcwd

url = (
    'https://api.open-meteo.com/v1/forecast'
    '?latitude=55.0344'
    '&longitude=82.9434'
    '&daily=sunrise,sunset,daylight_duration'
    '&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,temperature_80m,temperature_120m,wind_speed_10m,wind_speed_80m,wind_direction_10m,wind_direction_80m,visibility,evapotranspiration,weather_code,soil_temperature_0cm,soil_temperature_6cm,rain,showers,snowfall'
    '&timezone=auto'
    '&timeformat=unixtime'
    '&wind_speed_unit=kn'
    '&temperature_unit=fahrenheit'
    '&precipitation_unit=inch'
    '&start_date=2025-05-16'
    '&end_date=2025-05-30'
)

response = requests.get(url)
if response.status_code != 200: raise Exception('Could not get a responce')
data = response.json()

hourly_data = pd.DataFrame(data['hourly'])
hourly_data['day_index'] = hourly_data.index // 24
hourly_data['sunset'] = hourly_data['day_index'].map(lambda x: data['daily']['sunset'][x])
hourly_data['sunrise'] = hourly_data['day_index'].map(lambda x: data['daily']['sunrise'][x])
hourly_data['is_daylight'] = (hourly_data['time'] >= hourly_data['sunrise']) & (hourly_data['time'] <= hourly_data['sunset'])

def hmean(col):
    return hourly_data.groupby('day_index').mean()[col]

def hsum(col):
    return hourly_data.groupby('day_index').sum()[col]

def dhmean(col, fil = 'is_daylight'):
    return hourly_data[[col, 'day_index']][hourly_data[fil]].groupby('day_index').mean()[col]

def dhsum(col, fil='is_daylight'):
    return hourly_data[[col, 'day_index']][hourly_data[fil]].groupby('day_index').sum()[col]

digits_round = 3
absolute_zero = -273.15

def convert_to_days(col):
    new_list = []
    for i in range(0, len(col), 24):
        new_list.append(col[i:i+24].round(digits_round))
    return new_list

def knots_to_meters_per_sec(knots):
    return knots * 0.5144444444

def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5 / 9

def inches_to_mms(inches):
    return inches * 25.4

def feet_to_m(feet):
    return feet * 0.3048

# avgs
    # percentage
avg_relative_humidity_2m_24h = hmean('relative_humidity_2m')
    #temps (C)
avg_dew_point_2m_24h = fahrenheit_to_celsius(hmean('dew_point_2m'))
avg_apparent_temperature_24h = fahrenheit_to_celsius(hmean('apparent_temperature'))
avg_temperature_2m_24h = fahrenheit_to_celsius(hmean('temperature_2m'))
avg_temperature_80m_24h = fahrenheit_to_celsius(hmean('temperature_80m'))
avg_temperature_120m_24h = fahrenheit_to_celsius(hmean('temperature_120m'))
    # speed (m/s)
avg_wind_speed_10m_24h = knots_to_meters_per_sec(hmean('wind_speed_10m'))
avg_wind_speed_80m_24h = knots_to_meters_per_sec(hmean('wind_speed_80m'))
    # meters
avg_visibility_24h = feet_to_m(hmean('visibility'))
# sums
    # water (mm)
total_rain_24h = inches_to_mms(hsum('rain'))
total_showers_24h = inches_to_mms(hsum('showers'))
total_snowfall_24h = inches_to_mms(hsum('snowfall'))

# daylight
    # hours
daylight_hours = (pd.Series(data['daily']['sunset']) - np.array(data['daily']['sunrise'])) / 3600
#avgs
    # percentage
avg_relative_humidity_2m_daylight = dhmean('relative_humidity_2m')
    # temps (C)
avg_dew_point_2m_daylight = fahrenheit_to_celsius(dhmean('dew_point_2m'))
avg_apparent_temperature_daylight = fahrenheit_to_celsius(dhmean('apparent_temperature'))
avg_temperature_2m_daylight = fahrenheit_to_celsius(dhmean('temperature_2m'))
avg_temperature_80m_daylight = fahrenheit_to_celsius(dhmean('temperature_80m'))
avg_temperature_120m_daylight = fahrenheit_to_celsius(dhmean('temperature_120m'))
    # meters 
avg_visibility_daylight = feet_to_m(dhmean('visibility'))
    # speed (m/s)
avg_wind_speed_10m_daylight = knots_to_meters_per_sec(dhmean('wind_speed_10m'))
avg_wind_speed_80m_daylight = knots_to_meters_per_sec(dhmean('wind_speed_80m'))
# sums
    # water (mm)
total_rain_daylight = inches_to_mms(dhsum('rain'))
total_showers_daylight = inches_to_mms(dhsum('showers'))
total_snowfall_daylight = inches_to_mms(dhsum('snowfall'))

#conversions (into an array of (15, 25))
    # speed (m/s)
wind_speed_10m_m_per_s = convert_to_days(hourly_data['wind_speed_10m'].apply(knots_to_meters_per_sec))
wind_speed_80m_m_per_s = convert_to_days(hourly_data['wind_speed_80m'].apply(knots_to_meters_per_sec))
    # temps (C)
temperature_2m_celsius = convert_to_days(hourly_data['temperature_2m'].apply(fahrenheit_to_celsius))
apparent_temperature_celsius = convert_to_days(hourly_data['apparent_temperature'].apply(fahrenheit_to_celsius))
temperature_80m_celsius = convert_to_days(hourly_data['temperature_80m'].apply(fahrenheit_to_celsius))
temperature_120m_celsius = convert_to_days(hourly_data['temperature_120m'].apply(fahrenheit_to_celsius))
soil_temperature_0cm_celsius = convert_to_days(hourly_data['soil_temperature_0cm'].apply(fahrenheit_to_celsius).fillna(absolute_zero))
soil_temperature_6cm_celsius = convert_to_days(hourly_data['soil_temperature_6cm'].apply(fahrenheit_to_celsius).fillna(absolute_zero))
    # water (mm)
rain_mm = convert_to_days(hourly_data['rain'].apply(inches_to_mms))
showers_mm = convert_to_days(hourly_data['showers'].apply(inches_to_mms))
snowfall_mm = convert_to_days(hourly_data['snowfall'].apply(inches_to_mms))
    # time (ISO 8601)
sunset_iso = pd.to_datetime(pd.Series(data['daily']['sunset']), unit='s', origin='unix').apply(lambda x: x.tz_localize(data['timezone']).isoformat())
sunrise_iso = pd.to_datetime(pd.Series(data['daily']['sunrise']), unit='s', origin='unix').apply(lambda x: x.tz_localize(data['timezone']).isoformat())

data_dict = {
    # simple metrics per day
        # avgs
    "avg_relative_humidity_2m_24h": avg_relative_humidity_2m_24h,
    "avg_dew_point_2m_24h": avg_dew_point_2m_24h,
    "avg_apparent_temperature_24h": avg_apparent_temperature_24h,
    "avg_temperature_2m_24h": avg_temperature_2m_24h,
    "avg_temperature_80m_24h": avg_temperature_80m_24h,
    "avg_temperature_120m_24h": avg_temperature_120m_24h,
    "avg_wind_speed_10m_24h": avg_wind_speed_10m_24h,
    "avg_wind_speed_80m_24h": avg_wind_speed_80m_24h,
    "avg_visibility_24h": avg_visibility_24h,
        #sums
    "total_rain_24h": total_rain_24h,
    "total_showers_24h": total_showers_24h,
    "total_snowfall_24h": total_snowfall_24h,

    # simple metrics per day during daylight
    "daylight_hours": daylight_hours,
        #avgs
    "avg_relative_humidity_2m_daylight": avg_relative_humidity_2m_daylight,
    "avg_dew_point_2m_daylight": avg_dew_point_2m_daylight,
    "avg_apparent_temperature_daylight": avg_apparent_temperature_daylight,
    "avg_temperature_2m_daylight": avg_temperature_2m_daylight,
    "avg_temperature_80m_daylight": avg_temperature_80m_daylight,
    "avg_temperature_120m_daylight": avg_temperature_120m_daylight,
    "avg_visibility_daylight": avg_visibility_daylight,
    "avg_wind_speed_10m_daylight": avg_wind_speed_10m_daylight,
    "avg_wind_speed_80m_daylight": avg_wind_speed_80m_daylight,
        #sums
    "total_rain_daylight": total_rain_daylight,
    "total_showers_daylight": total_showers_daylight,
    "total_snowfall_daylight": total_snowfall_daylight,

    # converted hourly metrics
        # speed
    "wind_speed_10m_m_per_s": wind_speed_10m_m_per_s,
    "wind_speed_80m_m_per_s": wind_speed_80m_m_per_s,
        # temp
    "temperature_2m_celsius": temperature_2m_celsius,
    "apparent_temperature_celsius": apparent_temperature_celsius,
    "temperature_80m_celsius": temperature_80m_celsius,
    "temperature_120m_celsius": temperature_120m_celsius,
    "soil_temperature_0cm_celsius": soil_temperature_0cm_celsius,
    "soil_temperature_6cm_celsius": soil_temperature_6cm_celsius,
        # water
    "rain_mm": rain_mm,
    "showers_mm": showers_mm,
    "snowfall_mm": snowfall_mm,

    # ISO dates
    "sunset_iso": sunset_iso,
    "sunrise_iso": sunrise_iso
}
for i in data_dict:
    if not type(data_dict[i]) is list:
        data_dict[i] = data_dict[i].tolist()
path_csv = path.join(getcwd(), 'converted_meteorology_data.csv')
print(path_csv)
pd.DataFrame(data_dict).round(digits_round).to_csv(path_csv, index=False)
