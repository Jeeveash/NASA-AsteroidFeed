from flask import Flask, render_template, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='')

API_KEY = "hGapiSeLaWSU6Idgz1FrPFlsOguP0bey5aH3Ucq4"

class AsteroidDataCollector:
    def __init__(self, api_key):
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

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/asteroids')
def get_asteroids():
    collector = AsteroidDataCollector(api_key=API_KEY)
    return jsonify(collector.get_all_asteroids())

if __name__ == "__main__":
    app.run(debug=True)