from music21 import *
import csv
import os
import numpy as np
import pandas as pd
import json
from vizualizare_pattern import *

# Parametri
min_length = 3  # Lungimea minimă a tiparului (note)
max_length = 8  # Lungimea maximă a tiparului (note)
checked_patterns = set()  # Set global pentru a stoca tiparele deja verificate
output_file = "patterns.json"  # Fișierul unde salvăm rezultatele

def load_triplets(csv_file):
    """
    Încarcă notele din fișierul CSV și le organizează ca triplete (pitch, onset, duration) pentru fiecare voce.

    Args:
        csv_file (str): fisierul cu informatii despre notele piesei

    Return:
        voices (dict[str, list]): Un dicționar cu voci ca chei și liste de triplete ca valori.
    """
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Fișierul {csv_file} nu există.")
    
    df = pd.read_csv(csv_file)
    voices = {'Soprano': [], 'Alto': [], 'Tenor': [], 'Bass': []}
    current_voice = None
    
    for _, row in df.iterrows():
        if row['type'] == 'Instrument':
            current_voice = row['pitch']
        elif row['type'] == 'Note' and current_voice:
            try:
                pitch_num = int(row['pitch_num'])
                onset = float(row['offset'])
                duration = float(row['duration'])
                voices[current_voice].append((pitch_num, onset, duration))
            except (ValueError, KeyError) as e:
                print(f"Eroare la procesarea rândului {row}: {e}")
    
    for voice_name, triplets in voices.items():
        print(f"{voice_name}: {len(triplets)} note")
        if not triplets:
            print(f"Avertisment: Vocea {voice_name} este goală!")
    
    return voices

def triplets_to_intervals(triplets):
    """
    Transformă o secvență de note în intervale melodice (Δp, onset, duration).

    Args:
        triplets (list): lista de triplete (pitch, onset, duration)

    Return:
        intervals (list): Lista de intervale sub formă de tupluri (delta_p, onset, duration).
    """
    intervals = []
    for i in range(1, len(triplets)):
        delta_p = triplets[i][0] - triplets[i-1][0]
        intervals.append((delta_p, triplets[i][1], triplets[i][2]))
    return intervals

def delta_function(t1, t2):
    """
    Compară intervalele și duratele pentru notele intermediare.

    Args:
        t1 (tuple): primul interval (delta_p, onset, duration)
        t2 (tuple): al doilea interval (delta_p, onset, duration)

    Return:
        int: 1 dacă intervalele sunt similare, altfel 0.
    """
    (delta_p1, _, d1) = t1
    (delta_p2, _, d2) = t2
    if d1 != d2:
        return -np.inf
    if delta_p1 == delta_p2 or abs(delta_p1 - delta_p2) in [1]:
        return 1
    return 0

def delta_f_function(t1, t2):
    """
    Compară intervalele pentru ultima notă, ignorând durata.

    Args:
        t1 (tuple): primul interval (delta_p, onset, duration)
        t2 (tuple): al doilea interval (delta_p, onset, duration)

    Return:
        int: 1 dacă intervalele sunt similare, altfel 0.
    """
    (delta_p1, _, _) = t1
    (delta_p2, _, _) = t2
    if delta_p1 == delta_p2 or abs(delta_p1 - delta_p2) in [1]:
        return 1
    return 0

def similarity_function(pattern, voice):
    """
    Detectează aparițiile tiparului în voce folosind programare dinamică.

    Args:
        pattern (tuple): pattern-ul ales ca sursa
        voice (list): vocea în care căutăm pattern-ul

    Return:
        matches (list): Lista de potriviri găsite, fiecare potrivire conținând indexul și scorul.
    """
    m = len(pattern)
    n = len(voice)
    S = np.zeros((m + 1, n + 1))
    S_f = np.zeros((m + 1, n + 1))

    for b in range(n + 1):
        S[0, b] = 0
        S_f[0, b] = 0
    
    for a in range(1, m + 1):
        for b in range(1, n + 1):
            S[a, b] = S[a - 1, b - 1] + delta_function(pattern[a - 1], voice[b - 1])
            if a == m:
                S_f[m, b] = S[m - 1, b - 1] + delta_f_function(pattern[m - 1], voice[b - 1])

    matches = [(b, S_f[m, b]) for b in range(1, n + 1) if S_f[m, b] == m]
    return matches

def standardize_pattern_intervals(pattern_intervals):
    """
    Creează o reprezentare unică a unui tipar.

    Args:
        pattern_intervals (tuple):  pattern-ul sub forma de tuplu

    Return:
    tuple(standardized): tuplu pattern-ului doar cu delta_p si timp
    """
    standardized = [(delta_p, round(duration, 3)) for delta_p, _, duration in pattern_intervals]
    return tuple(standardized)

def calculate_end_notes(triplets):
    """
    Calculează poziția de final a unui pattern în note.

    Args:
        triplets (tuplu): lista de triplete (pitch, onset, duration) 

    Return:
        int: poziția de final a pattern-ului în note
    """
    return len(triplets) - 1

def evaluate_pattern_length(voices, source_voice, length, voice_order, start_pos=0):
    """
    Functie care evaluează lungimea unui pattern în diferite voci.

    Args:
        voices (dict): dicționar cu voci și tripletele lor
        source_voice (str): vocea sursă
        length (int): lungimea pattern-ului
        voice_order (list): ordinea vocii pentru căutare
        start_pos (int): poziția de start în vocea sursă

    Return:
        dict: informații despre pattern-ul găsit sau None
    """

    if len(voices[source_voice]) < start_pos + length:
        return None
    
    pattern_triplets = voices[source_voice][start_pos:start_pos + length]
    pattern_intervals = triplets_to_intervals(pattern_triplets)
    pattern_intervals_tuple = standardize_pattern_intervals(pattern_intervals)
    
    if pattern_intervals_tuple in checked_patterns:
        return None
    
    checked_patterns.add(pattern_intervals_tuple)
    
    pattern_onset = pattern_triplets[0][1] if pattern_triplets else None
    pattern_end_notes = calculate_end_notes(pattern_triplets)
    
    # Extrage intervalele melodice ale sursei (doar p2 - p1)
    source_intervals = [delta_p for delta_p, _, _ in pattern_intervals]
    
    total_matches = 0
    matches_by_voice = {}

    for voice_name in voice_order:
        intervals = triplets_to_intervals(voices[voice_name])
        matches = similarity_function(pattern_intervals, intervals)
        matches_by_voice[voice_name] = []
        
        # Colectăm toate potrivirile cu detalii
        voice_matches = []
        for b, score in matches:
            first_note_idx = max(0, b - (length - 1))
            last_note_idx = min(len(voices[voice_name]) - 1, b)
            matched_triplets = voices[voice_name][first_note_idx:last_note_idx + 1]
            if len(matched_triplets) < length:
                continue
            matched_onset = matched_triplets[0][1]
            if voice_name == source_voice and abs(matched_onset - pattern_onset) < 1e-6:
                continue
            matched_end_notes = calculate_end_notes(matched_triplets)
            matched_notes_names = [pitch.Pitch(p).nameWithOctave for p, _, _ in matched_triplets]
            matched_notes_midi = [p for p, _, _ in matched_triplets]
            matched_intervals = triplets_to_intervals(matched_triplets)
            matched_intervals_p = [delta_p for delta_p, _, _ in matched_intervals]
            interval_diff = sum(abs(p1 - p2) for p1, p2 in zip(source_intervals, matched_intervals_p)) if len(matched_intervals_p) == len(source_intervals) else float('inf')
            
            voice_matches.append({
                'onset': matched_onset,
                'end_notes': matched_end_notes,
                'num_notes': len(matched_triplets),
                'matched_notes': matched_notes_names,
                'matched_notes_midi': matched_notes_midi,
                'interval (p2 - p1, duration)': [(delta_p, round(duration, 3)) for delta_p, _, duration in matched_intervals],
                'interval_diff': interval_diff
            })
        
        # Filtrează potrivirile suprapuse în aceeași voce, păstrând cea mai apropiată de sursă
        voice_matches.sort(key=lambda x: (x['onset'], x['interval_diff']))
        filtered_matches = []
        i = 0
        while i < len(voice_matches):
            match = voice_matches[i]
            filtered_matches.append(match)
            end = match['onset'] + (match['num_notes'] - 1)
            i += 1
            while i < len(voice_matches) and voice_matches[i]['onset'] <= end:
                i += 1
            total_matches += 1
        matches_by_voice[voice_name] = filtered_matches
    
    return {
        'source_voice': source_voice,
        'length': length,
        'start_pos': start_pos,
        'pattern_onset': pattern_onset,
        'pattern_end_notes': pattern_end_notes,
        'pattern_num_notes': len(pattern_triplets),
        'total_matches': total_matches,
        'pattern_notes': [pitch.Pitch(p).nameWithOctave for p, _, _ in pattern_triplets],
        'pattern_notes_midi': [p for p, _, _ in pattern_triplets],
        'pattern_intervals': [(delta_p, d) for delta_p, _, d in pattern_intervals],
        'matches_by_voice': matches_by_voice
    } if total_matches > 0 else None



def save_results(results, voices, output_file, output_dir):
    """
    Salvează rezultatele în JSON.

    Args:
        results (list): Lista de rezultate de la evaluarea pattern-urilor.
        voices (dict): Dicționar cu voci ca chei și liste de triplete ca valori.
        output_file (str): Calea către fișierul de ieșire.
        output_dir (str): Directorul în care se salvează rezultatele.

    Return:
        json_data (list): Lista de date JSON pentru salvare.
    """
    json_data = []
    for result in results:
        if result is None or result['total_matches'] <= 0:  # Modificat pentru a include doar pattern-uri cu potriviri
            continue
        
        processed_matches_by_voice = {}
        for voice_name, matches_list in result['matches_by_voice'].items():
            processed_matches = []
            for match in matches_list:
                processed_matches.append({
                    'onset': match['onset'],
                    'end_notes': match['end_notes'],
                    'num_notes': match['num_notes'],
                    'matched_notes': [f"{note} ({midi})" for note, midi in zip(match['matched_notes'], match['matched_notes_midi'])],
                    'intervals (p2 - p1, duration)': ' '.join([f"({dp}, {dur})" for dp, dur in match['interval (p2 - p1, duration)']])
                })
            processed_matches_by_voice[voice_name] = processed_matches
        
        output_entry = {
            'pattern': {
                'source_voice': result['source_voice'],
                'intervals (p2 - p1, duration)': ' '.join([f"({dp}, {dur})" for dp, dur in result['pattern_intervals']]),
                'onset': result['pattern_onset'],
                'end_notes': result['pattern_end_notes'],
                'num_notes': result['pattern_num_notes'],
                'notes' : [f"{note} ({midi})" for note, midi in zip(result['pattern_notes'], result['pattern_notes_midi'])]
            },
            'total_matches': result['total_matches'],
            'matches': processed_matches_by_voice
        }
        json_data.append(output_entry)

    with open(output_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"Rezultatele au fost salvate în {output_file}.")
    
    return json_data

def find_pattern(csv_file, output_dir, partitura):
    """
    Rulează algoritmul pentru toate lungimile și pozițiile.

    Args:
        csv_file (str): Calea către fișierul CSV de intrare.
        output_dir (str): Directorul în care se salvează rezultatele.
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.
    """
    voices = load_triplets(csv_file)
    voice_order = ['Soprano', 'Alto', 'Tenor', 'Bass']
    
    results = []
    for source_voice in voice_order:
        voice_length = len(voices[source_voice])
        for length in range(min_length, max_length + 1):
            for start_pos in range(voice_length - length + 1):
                if len(voices[source_voice]) >= start_pos + length:
                    result = evaluate_pattern_length(voices, source_voice, length, voice_order, start_pos)
                    if result:
                        results.append(result)
    
    output_file = os.path.join(output_dir, "patterns.json")
    json_data = save_results(results, voices, output_file, output_dir)

    total_duration = int(partitura.flat.quarterLength) - 1
    generate_all_graphics(output_file, total_duration, output_dir)