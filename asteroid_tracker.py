# asteroid_tracker.py
from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime, timedelta
import os

app = Flask(__name__)

class AsteroidDataCollector:
    def __init__(self, api_key="DEMO_KEY"):
        self.api_key = api_key
        self.named_asteroids = [
            {
                "name": "Ceres",
                "diameter": 939.4,
                "is_dangerous": False,
                "first_observation": "1801-01-01",
                "description": "Largest object in the asteroid belt between Mars and Jupiter"
            },
            {
                "name": "Vesta",
                "diameter": 525.4,
                "is_dangerous": False,
                "first_observation": "1807-03-29",
                "description": "Second-most massive and second-largest body in the asteroid belt"
            },
            {
                "name": "Pallas",
                "diameter": 512,
                "is_dangerous": False,
                "first_observation": "1802-03-28",
                "description": "Third-largest asteroid in the asteroid belt"
            }
        ]

    def fetch_neo_feed(self, start_date=None, end_date=None):
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={self.api_key}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return self.process_neo_data(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NEO data: {e}")
            return []

    def process_neo_data(self, data):
        processed_asteroids = []
        
        for date in data['near_earth_objects']:
            for asteroid in data['near_earth_objects'][date]:
                processed_asteroids.append({
                    'name': asteroid['name'],
                    'diameter': self.calculate_average_diameter(asteroid),
                    'is_dangerous': asteroid['is_potentially_hazardous_asteroid'],
                    'first_observation': asteroid.get('orbital_data', {}).get('first_observation_date', 'Unknown'),
                    'velocity': asteroid['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']
                })
        
        return processed_asteroids

    def calculate_average_diameter(self, asteroid):
        estimated_diameter = asteroid['estimated_diameter']['meters']
        return (estimated_diameter['estimated_diameter_min'] + estimated_diameter['estimated_diameter_max']) / 2

    def get_all_asteroids(self):
        neo_asteroids = self.fetch_neo_feed()
        all_asteroids = self.named_asteroids + neo_asteroids
        
        named = sorted(
            [a for a in all_asteroids if a['name'] in [na['name'] for na in self.named_asteroids]],
            key=lambda x: x['diameter'],
            reverse=True
        )
        
        dangerous = sorted(
            [a for a in all_asteroids if a['is_dangerous'] and a['name'] not in [na['name'] for na in self.named_asteroids]],
            key=lambda x: x['diameter'],
            reverse=True
        )
        
        non_dangerous = sorted(
            [a for a in all_asteroids if not a['is_dangerous'] and a['name'] not in [na['name'] for na in self.named_asteroids]],
            key=lambda x: x['diameter'],
            reverse=True
        )
        
        return {
            'named': named,
            'dangerous': dangerous,
            'non_dangerous': non_dangerous
        }

# Create the templates directory and store the HTML template
def create_template_directory():
    os.makedirs('templates', exist_ok=True)
    with open('templates/index.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solar System Asteroid Tracker</title>
    <style>
        body {
            background-color: #000;
            color: #fff;
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            min-height: 100vh;
        }

        .container {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
        }

        h1 {
            text-align: center;
            color: #8a8a8a;
            margin-bottom: 40px;
        }

        .asteroid-section {
            margin-top: auto;
            padding: 20px 0;
        }

        .section-title {
            color: #666;
            margin-bottom: 20px;
        }

        .asteroid-container {
            display: flex;
            overflow-x: auto;
            gap: 20px;
            padding-bottom: 20px;
            scrollbar-width: thin;
            scrollbar-color: #666 #000;
        }

        .asteroid-container::-webkit-scrollbar {
            height: 8px;
        }

        .asteroid-container::-webkit-scrollbar-track {
            background: #000;
        }

        .asteroid-container::-webkit-scrollbar-thumb {
            background: #666;
            border-radius: 4px;
        }

        .asteroid-card {
            flex: 0 0 300px;
            background: rgba(50, 50, 50, 0.8);
            border: 1px solid #444;
            border-radius: 8px;
            padding: 20px;
            transition: transform 0.3s ease;
        }

        .asteroid-card:hover {
            transform: translateY(-5px);
        }

        .asteroid-card.named {
            background: rgba(70, 70, 100, 0.8);
        }

        .asteroid-card.dangerous {
            background: rgba(100, 50, 50, 0.8);
        }

        .asteroid-name {
            font-size: 1.2em;
            margin-bottom: 10px;
            color: #fff;
        }

        .asteroid-info {
            font-size: 0.9em;
            color: #bbb;
        }

        .danger-badge {
            display: inline-block;
            background: #ff4444;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Solar System Asteroid Tracker</h1>
        
        <div class="asteroid-section">
            <h2 class="section-title">All Asteroids</h2>
            <div class="asteroid-container" id="all-asteroids"></div>
        </div>
    </div>

    <script>
        async function fetchAsteroids() {
            try {
                const response = await fetch('/api/asteroids');
                const data = await response.json();
                renderAsteroids(data);
            } catch (error) {
                console.error('Error fetching asteroid data:', error);
            }
        }

        function renderAsteroids(data) {
            const container = document.getElementById('all-asteroids');
            const allAsteroids = [
                ...data.named,
                ...data.dangerous.sort((a, b) => b.diameter - a.diameter),
                ...data.non_dangerous.sort((a, b) => b.diameter - a.diameter)
            ];
            container.innerHTML = allAsteroids.map(asteroid => createAsteroidCard(asteroid)).join('');
        }

        function createAsteroidCard(asteroid) {
            const cardClass = ["Ceres", "Vesta", "Pallas"].includes(asteroid.name) ? 'named' : (asteroid.is_dangerous ? 'dangerous' : '');
            return `
                <div class="asteroid-card ${cardClass}">
                    <div class="asteroid-name">${asteroid.name}</div>
                    <div class="asteroid-info">
                        <p>Diameter: ${asteroid.diameter.toFixed(2)} meters</p>
                        <p>First Observed: ${asteroid.first_observation}</p>
                        ${asteroid.description ? `<p>${asteroid.description}</p>` : ''}
                        ${asteroid.velocity ? `<p>Velocity: ${parseFloat(asteroid.velocity).toFixed(2)} km/h</p>` : ''}
                        ${asteroid.is_dangerous ? '<div class="danger-badge">Potentially Hazardous</div>' : ''}
                    </div>
                </div>
            `;
        }

        // Initial load
        fetchAsteroids();
    </script>
</body>
</html>''')
        
# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/asteroids')
def get_asteroids():
    collector = AsteroidDataCollector(api_key=os.getenv('NASA_API_KEY', 'DEMO_KEY'))
    return jsonify(collector.get_all_asteroids())

if __name__ == "__main__":
    create_template_directory()
    app.run(debug=True)