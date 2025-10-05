document.addEventListener('DOMContentLoaded', () => {
    // Set current time and date
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    document.getElementById('currentDate').textContent = now.toLocaleDateString([], {day: 'numeric', month: 'short', year: 'numeric'});

    // Show default city
    showWeather('Pune');

    document.getElementById('searchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const city = document.getElementById('cityInput').value.trim();
        if (city) showWeather(city);
    });
});

async function showWeather(city) {
    hideError();
    setLoading(true);

    try {
        // Fetch weather
        const res = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
        if (!res.ok) {
            const errorData = await res.json();
            showError(errorData.error || 'City not found!');
            setLoading(false);
            return;
        }
        const data = await res.json();

        // Update main weather info
        document.getElementById('mainStatus').textContent = data.weather[0].main;
        document.getElementById('subStatus').textContent = data.weather[0].description;
        document.getElementById('mainTemp').textContent = `${Math.round(data.main.temp)}°`;
        document.getElementById('wind').textContent = `Wind: ${data.wind.speed} m/s`;
        document.getElementById('uv').textContent = `UV Index: 0 of 10`;
        document.getElementById('location').textContent = data.name;
        document.getElementById('humidity').textContent = `${data.main.humidity}%`;
        document.getElementById('weatherDetails').textContent = `Feels like ${Math.round(data.main.feels_like)}°C. Pressure: ${data.main.pressure} hPa.`;

        // Weather icon
        document.getElementById('weatherIcon').src = `https://openweathermap.org/img/wn/${data.weather[0].icon}@2x.png`;

        // Other cities (demo, you can fetch real data)
        document.getElementById('otherCities').innerHTML = `
            <div>Mumbai: <span>30°</span></div>
            <div>Delhi: <span>28°</span></div>
            <div>Bangalore: <span>25°</span></div>
            <div>Kolkata: <span>29°</span></div>
        `;

        // Fetch forecast for graph
        const forecastRes = await fetch(`/api/forecast?city=${encodeURIComponent(city)}`);
        if (!forecastRes.ok) {
            showError('No forecast data available.');
            setLoading(false);
            return;
        }
        const forecastData = await forecastRes.json();
        const today = new Date().toISOString().slice(0, 10);
        const hourly = forecastData.list.filter(item => item.dt_txt.startsWith(today));
        const temps = hourly.map(item => item.main.temp);
        const times = hourly.map(item => item.dt_txt.split(' ')[1].slice(0,5));
        const descs = hourly.map(item => item.weather[0].description);

        // Draw graph
        const ctx = document.getElementById('tempGraph').getContext('2d');
        if (window.tempChart) window.tempChart.destroy();
        window.tempChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: times,
                datasets: [{
                    label: 'Hourly Temperature (°C)',
                    data: temps,
                    backgroundColor: 'rgba(123,47,242,0.2)',
                    borderColor: '#FFD700',
                    borderWidth: 2,
                    pointBackgroundColor: '#FFD700',
                    tension: 0.3
                }]
            },
            options: {
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const i = context.dataIndex;
                                return `Temp: ${temps[i]}°C, ${descs[i]}`;
                            }
                        }
                    }
                },
                scales: {
                    y: { beginAtZero: false }
                }
            }
        });

        // Graph labels
        document.getElementById('graphLabels').innerHTML = `
            <span>LOW ${Math.min(...temps)}°C</span>
            <span>HIGH ${Math.max(...temps)}°C</span>
        `;

        setLoading(false);
    } catch (err) {
        showError('Network error!');
        setLoading(false);
    }
}

function showError(msg) {
    const errorDiv = document.getElementById('errorMsg');
    errorDiv.textContent = msg;
    errorDiv.style.display = 'block';
}
function hideError() {
    document.getElementById('errorMsg').style.display = 'none';
}
function setLoading(isLoading) {
    document.getElementById('mainStatus').textContent = isLoading ? 'Loading...' : '';
}