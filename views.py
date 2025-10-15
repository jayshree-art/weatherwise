from django.shortcuts import render
import requests
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_squared_error
from datetime import datetime, timedelta
import pytz
import os

# OpenWeatherMap API
API_KEY = "fc2ecbaacfea52c196fa734fec8ae490"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# ✅ Fetch Current Weather
def get_current_weather(city):
    if not city:
        return None

    url = f"{BASE_URL}?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ API Error ({response.status_code}): {response.text}")
        return None

    try:
        data = response.json()
    except ValueError:
        print("❌ Invalid JSON response:", response.text)
        return None

    return {
        'city': data['name'],
        'temperature': data['main']['temp'],
        'humidity': data['main']['humidity'],
        'description': data['weather'][0]['description'],
        'current_temp': round(data['main']['temp']),
        'feels_like': round(data['main']['feels_like']),
        'temp_min': round(data['main']['temp_min']),
        'temp_max': round(data['main']['temp_max']),
        'country': data['sys']['country'],
        'wind_gust_dir': data['wind']['deg'],
        'pressure': data['main']['pressure'],
        'Wind_Gust_Speed': data['wind']['speed'],
        'clouds': data['clouds']['all'],
        'Visibility': data.get('visibility', 0)
    }


# ✅ Read Historical Data
def read_historical_data(filename):
    df = pd.read_csv(filename)
    df = df.dropna().drop_duplicates()
    return df


# ✅ Prepare Data for ML Models
def prepare_data(data):
    le = LabelEncoder()
    data['WindGustDir'] = le.fit_transform(data['WindGustDir'])
    data['RainTomorrow'] = le.fit_transform(data['RainTomorrow'])

    X = data[['MinTemp', 'MaxTemp', 'WindGustDir', 'WindGustSpeed', 'Humidity', 'Pressure', 'Temp']]
    y = data['RainTomorrow']
    return X, y, le


# ✅ Train Rain Classifier Model
def train_rain_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print("✅ Rain model trained (MSE:", mean_squared_error(y_test, model.predict(X_test)), ")")
    return model


# ✅ Prepare Regression Data
def prepare_regression_data(data, feature):
    x, y = [], []
    for i in range(len(data) - 1):
        x.append(data[feature].iloc[i])
        y.append(data[feature].iloc[i + 1])
    x = np.array(x).reshape(-1, 1)
    y = np.array(y)
    return x, y


# ✅ Train Regression Model
def train_regression_model(x, y):
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(x, y)
    return model


# ✅ Predict Future (Next 5 hours)
def predict_future(model, current_value):
    prediction = [current_value]
    for _ in range(5):
        next_value = model.predict(np.array(prediction[-1]).reshape(-1, 1))
        prediction.append(next_value[0])
    return prediction[1:]


# ✅ Main Weather View
def weather_view(request):
    context = {}

    if request.method == 'POST':
        city = request.POST.get('city')
        current_weather = get_current_weather(city)

        if not current_weather:
            context['error'] = f"⚠️ Could not fetch weather for '{city}'. Please try another city."
            return render(request, 'weather.html', context)

        # --- Load historical data if available ---
        csv_path = os.path.join(os.path.dirname(__file__), 'weather.csv')

        if os.path.exists(csv_path):
            historical_data = read_historical_data(csv_path)
            X, y, le = prepare_data(historical_data)
            rain_model = train_rain_model(X, y)

            # Predict rain possibility (optional future upgrade)
            current_df = pd.DataFrame([{
                'MinTemp': current_weather['temp_min'],
                'MaxTemp': current_weather['temp_max'],
                'WindGustDir': 0,
                'WindGustSpeed': current_weather['Wind_Gust_Speed'],
                'Humidity': current_weather['humidity'],
                'Pressure': current_weather['pressure'],
                'Temp': current_weather['current_temp']
            }])
            rain_prediction = rain_model.predict(current_df)[0]
        else:
            print("⚠️ weather.csv not found, skipping ML forecast.")
            rain_prediction = None

        # --- Future prediction for Temp & Humidity ---
        if os.path.exists(csv_path):
            x_temp, y_temp = prepare_regression_data(historical_data, 'Temp')
            x_hum, y_hum = prepare_regression_data(historical_data, 'Humidity')

            temp_model = train_regression_model(x_temp, y_temp)
            hum_model = train_regression_model(x_hum, y_hum)

            future_temp = predict_future(temp_model, current_weather['temp_min'])
            future_humidity = predict_future(hum_model, current_weather['humidity'])
        else:
            # fallback (no CSV)
            future_temp = [current_weather['current_temp'] + i for i in range(1, 6)]
            future_humidity = [current_weather['humidity'] - i for i in range(1, 6)]

        # --- Generate future times ---
        timezone = pytz.timezone('Asia/Kolkata')
        now = datetime.now(timezone)
        next_hour = now + timedelta(hours=1)
        next_hour = next_hour.replace(minute=0, second=0, microsecond=0)
        future_time = [(next_hour + timedelta(hours=i)).strftime("%I:%M %p") for i in range(5)]

        # --- Combine all data ---
        context.update({
            **current_weather,
            'time': now.strftime("%I:%M %p"),
            'date': now.strftime("%B %d, %Y"),
            'rain_prediction': rain_prediction,
            'time1': future_time[0], 'time2': future_time[1], 'time3': future_time[2],
            'time4': future_time[3], 'time5': future_time[4],
            'temp1': round(future_temp[0], 1), 'temp2': round(future_temp[1], 1),
            'temp3': round(future_temp[2], 1), 'temp4': round(future_temp[3], 1),
            'temp5': round(future_temp[4], 1),
            'hum1': round(future_humidity[0], 1), 'hum2': round(future_humidity[1], 1),
            'hum3': round(future_humidity[2], 1), 'hum4': round(future_humidity[3], 1),
            'hum5': round(future_humidity[4], 1)
        })

    return render(request, 'weather.html', context)
