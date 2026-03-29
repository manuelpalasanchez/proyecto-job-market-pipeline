from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from sqlalchemy import create_engine, engine, text

def geocode_missing_locations(engine):
    geolocator = Nominatim(user_agent="job_market_pipeline")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT location 
            FROM jobs 
            WHERE location IS NOT NULL 
            AND latitud IS NULL
        """))
        cities = [row[0] for row in result.fetchall()]

    print(f"Ciudades a geocodificar: {len(cities)}")

    with engine.connect() as conn:
        for city in cities:
            try:
                location = geocode(f"{city}, España")
                if location:
                    conn.execute(text("""
                        UPDATE jobs 
                        SET latitud = :lat, longitud = :lon
                        WHERE location = :city
                    """), {"lat": location.latitude, "lon": location.longitude, "city": city})
                    print(f"{city}: {location.latitude}, {location.longitude}")
                else:
                    print(f"{city}: no encontrada")
            except Exception as e:
                print(f"{city}: error - {e}")

        conn.commit()

    print("Geocodificación completada")