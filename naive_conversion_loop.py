import requests
import numpy as np
import json
import pandas as pd

from os import path, getcwd

default_url = ('https://api.open-meteo.com/v1/forecast'
            '?latitude=55.0344'
            '&longitude=82.9434'
            '&daily=sunrise,sunset,daylight_duration'
            '&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,temperature_80m,temperature_120m,wind_speed_10m,wind_speed_80m,wind_direction_10m,wind_direction_80m,visibility,evapotranspiration,weather_code,soil_temperature_0cm,soil_temperature_6cm,rain,showers,snowfall'
            '&timezone=auto'
            '&timeformat=unixtime'
            '&wind_speed_unit=kn'
            '&temperature_unit=fahrenheit'
            '&precipitation_unit=inch')

while True:   # Handle correct json request
    url = input('Write the json request, if "No", the default request will be used\nTo input custom data, write "Date"\n')

    if url == '' or url.lower() == 'no':    # Default url with default dates
        url = default_url + '&start_date=2025-05-16' + '&end_date=2025-05-30'

    elif url.lower() == 'date':   # Handle custon dates
        url = input('Write the json requet without dates, if "No", the default request without dates will be used\n')

        if url == '' or url.lower() == 'no':    # Default url with custom dates
            url = default_url

        url += '&start_date=' + input('Write the start date in the format 2025-10-30\n')
        url += '&end_date=' + input('Write the end date in the format 2025-10-30\n')

    try:
        response = requests.get(url)
        if response.status_code == 200:   # Default succeess code
            print('Success!')
            break
        else:
            print('Something went wrong, status code:', responce.status_code)
    except:
        print('Invalid URL')
    print()
try:
    data = response.json()
except ValueError:
    print("Failed to decode JSON")

hourly_data = pd.DataFrame(data['hourly'])
hourly_data['day_index'] = hourly_data.index // 24
hourly_data['sunset'] = hourly_data['day_index'].map(lambda x: data['daily']['sunset'][x])
hourly_data['sunrise'] = hourly_data['day_index'].map(lambda x: data['daily']['sunrise'][x])
hourly_data['is_daylight'] = (hourly_data['time'] >= hourly_data['sunrise']) & (hourly_data['time'] <= hourly_data['sunset'])


absolute_zero = -273.15

metrics_suffixes = ('_celsius', '_m_per_s', '_mm')
filter_suffixes = ('_daylight', '_24h')
operation_prefixes = ('avg_', 'total_')
no_conversion = ('iso', 'humidity', 'hours')
no_operation = ('iso', 'hours')

def search_for(string, array):
    for value in array:
        if value in string:
            return True
    return False

def clear_from(string, array):
    for value in array:
        string = string.replace(value, '')
    return string

def column_mean(column, filter_column=''):
    if filter_column:
        return hourly_data[[column, 'day_index']][hourly_data[filter_column]].groupby('day_index').mean()[column]
    else:
        return hourly_data.groupby('day_index').mean()[column]

def column_sum(column, filter_column=''):
    if filter_column:
        return hourly_data[[column, 'day_index']][hourly_data[filter_column]].groupby('day_index').sum()[column]
    else:
        return hourly_data.groupby('day_index').sum()[column]

def smart_column_operation(varname, filter_column):
    column = clear_from(varname, [*metrics_suffixes, *filter_suffixes, *operation_prefixes])
    if search_for(varname, no_operation):
        return []
    elif 'avg' in varname:
        return column_mean(column, filter_column)
    elif 'total' in varname:
        return column_sum(column, filter_column)
    else:
        return hourly_data[column]

digits_round = 3

def knots_to_meters_per_sec(knots):
    return knots * 0.5144444444

def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5 / 9

def inches_to_mms(inches):
    return inches * 25.4

def feet_to_m(feet):
    return feet * 0.3048

def convert_to_days(col):
    new_list = []
    for i in range(0, len(col), 24):
        new_list.append(col[i:i+24].round(digits_round))
    return new_list

def smart_metrics_convert(varname, value):
    if search_for(varname, no_conversion):
        if type(value) is list:
            return value
        else:
            value = value.fillna(-1)

    elif 'temperature' in varname or 'dew_point' in varname:
        value = fahrenheit_to_celsius(value).fillna(absolute_zero)

    elif 'speed' in varname:
        value = knots_to_meters_per_sec(value).fillna(-1)

    elif 'visibility' in varname:
        value = feet_to_m(value).fillna(-1)

    else:
        value = inches_to_mms(value).fillna(-1)

    return value.round(digits_round)

data_dict = {
    # Simple metrics per day
        # Averages
    "avg_relative_humidity_2m_24h": [],
    "avg_dew_point_2m_24h": [],
    "avg_apparent_temperature_24h": [],
    "avg_temperature_2m_24h": [],
    "avg_temperature_80m_24h": [],
    "avg_temperature_120m_24h": [],
    "avg_wind_speed_10m_24h": [],
    "avg_wind_speed_80m_24h": [],
    "avg_visibility_24h": [],

        # Sums
    "total_rain_24h": [],
    "total_showers_24h": [],
    "total_snowfall_24h": [],

    # Simple metrics per day during daylight
    "daylight_hours": [],
        # Averages
    "avg_relative_humidity_2m_daylight": [],
    "avg_dew_point_2m_daylight": [],
    "avg_apparent_temperature_daylight": [],
    "avg_temperature_2m_daylight": [],
    "avg_temperature_80m_daylight": [],
    "avg_temperature_120m_daylight": [],
    "avg_visibility_daylight": [],
    "avg_wind_speed_10m_daylight": [],
    "avg_wind_speed_80m_daylight": [],
        # Sums
    "total_rain_daylight": [],
    "total_showers_daylight": [],
    "total_snowfall_daylight": [],

    # Converted hourly metrics
        # Speed
    "wind_speed_10m_m_per_s": [],
    "wind_speed_80m_m_per_s": [],
        # Temperature
    "temperature_2m_celsius": [],
    "apparent_temperature_celsius": [],
    "temperature_80m_celsius": [],
    "temperature_120m_celsius": [],
    "soil_temperature_0cm_celsius": [],
    "soil_temperature_6cm_celsius": [],
        # Water
    "rain_mm": [],
    "showers_mm": [],
    "snowfall_mm": [],

    # ISO dates
    "sunset_iso": [],
    "sunrise_iso": []
}

for varname in data_dict:
    filter_column = 'is_daylight' if 'daylight' in varname else ''

    data_dict[varname] = smart_metrics_convert(varname, smart_column_operation(varname, filter_column))

    if search_for(varname, metrics_suffixes):
        data_dict[varname] = convert_to_days(data_dict[varname])
  
na_fill_iso = pd.to_datetime(0, unit='s', origin='unix').tz_localize(data['timezone']).isoformat()

for i in ('sunset', 'sunrise'):
    data_dict[i + '_iso'] = pd.to_datetime(pd.Series(data['daily'][i]), unit='s', origin='unix').apply(lambda x: x.tz_localize(data['timezone']).isoformat()).fillna(na_fill_iso)

data_dict['daylight_hours'] = ((pd.Series(data['daily']['sunset']) - np.array(data['daily']['sunrise'])) / 3600).fillna(-1)

for i in data_dict:
    if not type(data_dict[i]) is list:
        data_dict[i] = data_dict[i].tolist()

path_csv = path.join(getcwd(), 'converted_meteorology_data.csv')
print(path_csv)
pd.DataFrame(data_dict).round(digits_round).to_csv(path_csv, index=False)
