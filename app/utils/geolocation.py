from math import radians, sin, cos, sqrt, atan2

CITY_COORDINATES = {
    'Cascavel': (-24.9555, -53.4552),
    'Curitiba': (-25.4284, -49.2733),
    'Toledo': (-24.7246, -53.7412),
    'Foz do Iguaçu': (-25.5478, -54.5882),
}


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c



def resolve_user_location(user=None, city=None):
    if user and user.latitude is not None and user.longitude is not None:
        return {
            'city': user.city,
            'latitude': user.latitude,
            'longitude': user.longitude,
        }

    city_name = city or (user.city if user else None) or 'Cascavel'
    lat, lon = CITY_COORDINATES.get(city_name, CITY_COORDINATES['Cascavel'])
    return {
        'city': city_name,
        'latitude': lat,
        'longitude': lon,
    }
