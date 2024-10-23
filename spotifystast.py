import json
from collections import Counter
from datetime import datetime

# Load data from multiple files in the same folder
def load_multiple_files(file_paths):
    all_data = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_data.extend(data)  # Append the data from each file
    return all_data

def count_occurrences(data):
    track_counter = Counter()
    artist_counter = Counter()
    album_counter = Counter()
    skipped_counter = Counter()

    for entry in data:
        # Track name
        track_name = entry.get('master_metadata_track_name', 'Unknown Track')
        # Artist name
        artist_name = entry.get('master_metadata_album_artist_name', 'Unknown Artist')
        # Album name
        album_name = entry.get('master_metadata_album_album_name', 'Unknown Album')

        # Increment counters
        track_counter[(track_name, artist_name)] += 1  # Count track by (name, artist)
        artist_counter[artist_name] += 1
        album_counter[album_name] += 1

        # If the song was skipped, increment the skipped counter
        if entry.get('skipped'):
            skipped_counter[track_name] += 1

    return track_counter, artist_counter, album_counter, skipped_counter

# Function to get the top N items from a counter
def get_top_n(counter, n):
    return counter.most_common(n)

def save_to_file(file_name, top_artists, top_songs, top_albums, top_skipped_songs, top_intentional_songs):
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write("Top Artists:\n")
        for i, (artist, count) in enumerate(top_artists, start=1):
            f.write(f"{i}- {artist}: {count} times\n")
        
        f.write("\nTop Songs:\n")
        for i, ((song, artist), count) in enumerate(top_songs, start=1):
            f.write(f"{i}- {song} by {artist}: {count} times\n")
        
        f.write("\nTop Albums:\n")
        for i, (album, count) in enumerate(top_albums, start=1):
            f.write(f"{i}- {album}: {count} times\n")
        
        f.write("\nTop Skipped Songs:\n")
        for i, (skipped_song, count) in enumerate(top_skipped_songs, start=1):
            f.write(f"{i}- {skipped_song}: {count} times\n")
        
        f.write("\nTop Intentional Songs:\n")
        for i, (intentional_song, count) in enumerate(top_intentional_songs, start=1):
            f.write(f"{i}- {intentional_song}: {count} times\n")


def process_data_and_save_to_file(data, file_name, top_artists=50, top_songs=100, top_albums=50, top_skipped_songs=10, top_intentional_songs=10, since_beginning_of_year=False):
    if since_beginning_of_year:
        current_year = datetime.now().year
        data = filter_data_by_year(data, current_year)
    
    filtered_data = [
        entry for entry in data if (
            entry.get('master_metadata_track_name') is not None and
            entry.get('master_metadata_album_artist_name') is not None and
            entry.get('master_metadata_album_album_name') is not None
        )
    ]
    
    track_counter, artist_counter, album_counter, skipped_counter = count_occurrences(filtered_data)

    # Get top results
    top_artists_list = get_top_n(artist_counter, top_artists)
    top_songs_list = get_top_n(track_counter, top_songs)
    top_albums_list = get_top_n(album_counter, top_albums)
    top_skipped_songs_list = get_top_n(skipped_counter, top_skipped_songs)

    # Calculate intentional songs
    intentional_songs_counter = calculate_most_played_songs(data)
    top_intentional_songs_list = get_top_n(intentional_songs_counter, top_intentional_songs)

    # Save to file
    save_to_file(file_name, top_artists_list, top_songs_list, top_albums_list, top_skipped_songs_list, top_intentional_songs_list)


def calculate_listening_by_day_of_week(data):
    day_counter = Counter()

    for entry in data:
        timestamp = entry.get('ts', None)
        if timestamp:
            day_of_week = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").strftime('%A')
            day_counter[day_of_week] += 1

    return day_counter

def calculate_active_hours(data):
    hour_counter = Counter()

    for entry in data:
        timestamp = entry.get('ts', None)
        if timestamp:
            hour = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").hour
            
            # Define time ranges in 24-hour format
            if 5 <= hour < 12:  # Morning: 5 AM to 11:59 AM
                hour_counter['Morning (05:00 - 11:59)'] += 1
            elif 12 <= hour < 17:  # Afternoon: 12 PM to 4:59 PM
                hour_counter['Afternoon (12:00 - 16:59)'] += 1
            elif 17 <= hour < 21:  # Evening: 5 PM to 8:59 PM
                hour_counter['Evening (17:00 - 20:59)'] += 1
            else:  # Night: 9 PM to 4:59 AM
                hour_counter['Night (21:00 - 04:59)'] += 1

    return hour_counter

# Function to calculate listening by country
def calculate_listening_by_country(data):
    country_counter = Counter()

    for entry in data:
        country = entry.get('conn_country', None)
        if country:
            country_counter[country] += 1

    return country_counter

# Function to calculate most played songs (intentionally)
def calculate_most_played_songs(data):
    song_counter = Counter()

    for entry in data:
        reason_start = entry.get('reason_start', None)
        track_name = entry.get('master_metadata_track_name', None)
        
        # Count only if the play reason indicates intentional play
        if reason_start == 'clickrow' and track_name:  # Focused on clickrow
            song_counter[track_name] += 1

    return song_counter

def filter_data_by_year(data, year):
    """ Filter the data to only include entries from the specified year. """
    filtered_data = []
    for entry in data:
        timestamp = entry.get('ts', None)
        if timestamp:
            entry_year = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").year
            if entry_year == year:
                filtered_data.append(entry)
    return filtered_data

def get_all_songs_by_artist(data, artist_name):
    """ Get all songs and albums by a specific artist. """
    song_counter = {}
    album_counter = {}

    # Count occurrences of each song and album by the specified artist
    for entry in data:
        if entry.get('master_metadata_album_artist_name') == artist_name:
            song_title = entry.get('master_metadata_track_name')
            album_name = entry.get('master_metadata_album_album_name')
            if song_title:
                # Count songs
                song_counter[song_title] = song_counter.get(song_title, 0) + 1
                # Count albums
                if album_name:
                    album_counter[album_name] = album_counter.get(album_name, 0) + 1

    # Return sorted lists of songs and albums
    sorted_songs = sorted(song_counter.items(), key=lambda x: x[1], reverse=True)
    sorted_albums = sorted(album_counter.items(), key=lambda x: x[1], reverse=True)
    return sorted_songs, sorted_albums

def save_all_songs_by_artist(file_name, artist_name, all_songs, all_albums):
    """ Save all songs and albums of a specific artist to a file. """
    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(f"All Songs by {artist_name}:\n")
        for i, (song, count) in enumerate(all_songs, start=1):
            f.write(f"{i}- {song}: {count} times\n")

        f.write(f"\nTop Albums by {artist_name}:\n")
        for i, (album, count) in enumerate(all_albums, start=1):
            f.write(f"{i}- {album}: {count} times\n")

# Main execution
if __name__ == "__main__":
    file_paths = ['1.json', '2.json', '3.json', '4.json', '5.json', '6.json']  # Files are in the same folder as the script
    output_file = "spotify_top_stats.txt"  # Output file name
    data = load_multiple_files(file_paths)
    #process_data_and_save_to_file(data, output_file, since_beginning_of_year=True)
    process_data_and_save_to_file(data, output_file)

    day_of_week_stats = calculate_listening_by_day_of_week(data)
    print("Listening Stats by Day of the Week:")
    for day, count in day_of_week_stats.most_common():
        print(f"{day}: {count} times")
    print("------------------------")
    hour_stats = calculate_active_hours(data)
    print("Listening Stats by Time of Day:")
    for period, count in hour_stats.items():
        print(f"{period}: {count} times")
        # Calculate and display listening by country
    country_stats = calculate_listening_by_country(data)
    print("\nListening Stats by Country:")
    for country, count in country_stats.most_common():
        print(f"{country}: {count} times")
    artist_name = "Playboi Carti"  # Replace with the actual artist's name
    file_name = f"{artist_name}_all_songs.txt"
    all_songs, all_albums = get_all_songs_by_artist(data, artist_name)
    save_all_songs_by_artist(file_name, artist_name, all_songs, all_albums)
