import math
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Trip:
    trip_id: str
    traveler_id: str
    origin_coords: tuple[float, float]
    destination_coords: tuple[float, float]
    max_detour_km: float
    available_volume_liters: float

@dataclass
class Parcel:
    parcel_id: str
    sender_id: str
    pickup_coords: tuple[float, float]
    dropoff_coords: tuple[float, float]
    volume_liters: float
    weight_kg: float

def haversine_km(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
    """Calculate great-circle distance between two (lat, lon) points in kilometers."""
    R = 6371.0
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def calculate_dynamic_fee(distance_km: float, weight_kg: float) -> Dict[str, float]:
    """Compute peer-to-peer delivery fee and platform commission split."""
    base_fee = 4.50
    distance_rate = 0.12 * distance_km
    weight_surcharge = 0.50 * max(0.0, weight_kg - 2.0)
    total_price = round(base_fee + distance_rate + weight_surcharge, 2)
    platform_commission = round(total_price * 0.15, 2)
    traveler_payout = round(total_price - platform_commission, 2)
    return {
        "total_price_eur": total_price,
        "traveler_payout_eur": traveler_payout,
        "platform_commission_eur": platform_commission,
    }

def match_parcel_to_trips(parcel: Parcel, active_trips: List[Trip]) -> List[Dict]:
    """Find and rank compatible trips based on detour threshold and capacity."""
    matches = []
    direct_parcel_km = haversine_km(parcel.pickup_coords, parcel.dropoff_coords)

    for trip in active_trips:
        if trip.available_volume_liters < parcel.volume_liters:
            continue

        base_trip_km = haversine_km(trip.origin_coords, trip.destination_coords)
        detour_trip_km = (
            haversine_km(trip.origin_coords, parcel.pickup_coords)
            + direct_parcel_km
            + haversine_km(parcel.dropoff_coords, trip.destination_coords)
        )
        added_detour = round(detour_trip_km - base_trip_km, 2)

        if added_detour <= trip.max_detour_km:
            pricing = calculate_dynamic_fee(direct_parcel_km, parcel.weight_kg)
            matches.append({
                "trip_id": trip.trip_id,
                "traveler_id": trip.traveler_id,
                "added_detour_km": added_detour,
                "pricing": pricing,
            })

    return sorted(matches, key=lambda x: x["added_detour_km"])

if __name__ == "__main__":
    sample_trips = [
        Trip("TRP-101", "USR-88", (48.8566, 2.3522), (45.7640, 4.8357), max_detour_km=15.0, available_volume_liters=40.0),
        Trip("TRP-102", "USR-42", (48.8566, 2.3522), (43.2965, 5.3698), max_detour_km=10.0, available_volume_liters=25.0),
    ]
    sample_parcel = Parcel("PCL-501", "USR-19", (48.8606, 2.3376), (45.7578, 4.8320), volume_liters=15.0, weight_kg=4.5)
    print(match_parcel_to_trips(sample_parcel, sample_trips))
