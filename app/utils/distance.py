import pandas as pd
import numpy as np

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance in kilometers between two points using the Haversine formula.
    """
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    c = 2*np.arcsin(np.sqrt(a))
    return R * c

# def filter_points_by_distance(df, ref_lat, ref_lon, min_km=0, max_km=70):
#     """
#     df: pandas DataFrame with 'Latitude' and 'Longitude' columns
#     ref_lat, ref_lon: reference point coordinates
#     min_km, max_km: distance range in km
#     Returns: DataFrame of points within the distance range, sorted by distance
#     """
#     df = df.copy()
#     df['Distance_km'] = df.apply(lambda row: haversine_distance(ref_lat, ref_lon, row['Latitude'], row['Longitude']), axis=1)
#     filtered = df[(df['Distance_km'] >= min_km) & (df['Distance_km'] <= max_km)]
#     return filtered.sort_values('Distance_km').reset_index(drop=True)

def sort_events_by_distance(events_df, pincodes_df, user_lat, user_lon, max_distance_km=70):
    """
    Sort events by distance from user's location.

    Args:
        events_df: DataFrame with event data including 'pincode' column
        pincodes_df: DataFrame with pincode data including 'pincode', 'latitude', 'longitude' columns
        user_lat, user_lon: User's latitude and longitude
        max_distance_km: Maximum distance to consider (default 70km)

    Returns:
        DataFrame: Events sorted by distance, with Distance_km column added
    """
    # Merge events with pincode data to get lat/lng for each event
    events_with_location = events_df.merge(
        pincodes_df[['pincode', 'latitude', 'longitude']],
        on='pincode',
        how='left'
    )

    # Drop events that don't have location data
    events_with_location = events_with_location.dropna(subset=['latitude', 'longitude'])

    # Calculate distance for each event
    events_with_location['Distance_km'] = events_with_location.apply(
        lambda row: haversine_distance(user_lat, user_lon, row['latitude'], row['longitude']),
        axis=1
    )

    # Filter by maximum distance and sort
    filtered_events = events_with_location[events_with_location['Distance_km'] <= max_distance_km]
    sorted_events = filtered_events.sort_values('Distance_km').reset_index(drop=True)

    return sorted_events

# import pandas as pd

# # Mock dataset
# data = pd.DataFrame({
#     'District': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
#     'StateName': ['X']*12,
#     'Latitude': [28.7, 28.5, 28.9, 28.6, 28.8, 29.0, 28.65, 28.75, 28.85, 28.55, 28.95, 28.66],
#     'Longitude':[77.2,77.3,77.1,77.25,77.15,77.35,77.28,77.18,77.22,77.05,77.4,77.33],
#     'Pincode':[1001,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1012]
# })

# ref_lat, ref_lon = 28.6139, 77.2090  # Reference: Delhi

# result = filter_points_by_distance(data, ref_lat, ref_lon, min_km=0, max_km=250)
# print(result[['District','Latitude','Longitude','Distance_km']])

