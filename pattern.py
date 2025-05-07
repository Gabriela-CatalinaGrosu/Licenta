from music21 import *
import csv
import os
import numpy as np
import pandas as pd
import json

# Parametri
csv_file = "bwv66.6.csv"
min_length = 3  # Lungimea minimă a tiparului (note)
max_length = 8  # Lungimea maximă a tiparului (note)
checked_patterns = set()  # Set global pentru a stoca tiparele deja verificate
output_file = "results.json"  # Fișierul unde salvăm rezultatele

def load_triplets(csv_file):
    """
    Încarcă notele din fișierul CSV și le organizează ca triplete (pitch, onset, duration) pentru fiecare voce.
    Input: Calea către fișierul CSV.
    Output: Dicționar cu vocile (Soprano, Alto, Tenor, Bass) și listele lor de triplete.
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
    
    # Verificăm dacă vocile conțin date
    for voice_name, triplets in voices.items():
        print(f"{voice_name}: {len(triplets)} note")
        if not triplets:
            print(f"Avertisment: Vocea {voice_name} este goală!")
    
    return voices

def triplets_to_intervals(triplets):
    """
    Transformă o secvență de note (triplete) în intervale melodice (Δp, onset, duration).
    Input: Lista de triplete (pitch, onset, duration).
    Output: Lista de triplete (Δp, onset, duration), unde Δp = p_i - p_{i-1}.
    """
    intervals = []
    for i in range(1, len(triplets)):
        delta_p = triplets[i][0] - triplets[i-1][0]
        intervals.append((delta_p, triplets[i][1], triplets[i][2]))
    return intervals

def delta_function(t1, t2):
    """
    Compară intervalele și duratele pentru notele intermediare.
    Input: Două triplete (Δp, onset, duration).
    Output: +1 dacă intervalele sunt similare și duratele egale, -∞ dacă duratele diferă, 0 altfel.
    """
    (delta_p1, _, d1) = t1
    (delta_p2, _, d2) = t2

    if d1 != d2:
        return -np.inf
    
    if delta_p1 == delta_p2:
        return 1
    
    if delta_p1 - delta_p2 in [-1, 1]:
        return 1

    return 0

def delta_f_function(t1, t2):
    """
    Compară intervalele pentru ultima notă, ignorând durata.
    Input: Două triplete (Δp, onset, duration).
    Output: +1 dacă intervalele sunt similare, 0 altfel.
    """
    (delta_p1, _, _) = t1
    (delta_p2, _, _) = t2

    if delta_p1 == delta_p2:
        return 1
    
    if delta_p1 - delta_p2 in [-1, 1]:
        return 1

    return 0

def similarity_function(pattern, voice):
    """
    Detectează aparițiile tiparului în voce folosind programare dinamică.
    Input:
        - pattern: Lista de triplete (Δp, onset, duration) pentru tipar.
        - voice: Lista de triplete pentru voce.
        - threshold: Scor minim pentru potriviri.
    Output: Lista de tupluri (b, score), unde b este indicele notei finale și score este S_f[m, b].
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
    Creează o reprezentare unică a unui tipar bazată pe (Δp, durată).
    Input: Lista de intervale [(Δp, onset, durată)].
    Output: Tuplu unic hashabil care reprezintă tiparul.
    """
    standardized = [(delta_p, round(duration, 3)) for delta_p, _, duration in pattern_intervals]
    return tuple(standardized)

def evaluate_pattern_length(voices, source_voice, length, voice_order, start_pos=0):
    """
    Evaluează un tipar de o anumită lungime dintr-o voce sursă, începând de la o poziție dată.
    Input:
        - voices: Dicționar cu vocile și tripletele lor.
        - source_voice: Vocea din care se extrage tiparul (Soprano, Alto, Tenor, Bass).
        - length: Numărul de note al tiparului.
        - voice_order: Lista cu ordinea vocilor.
        - start_pos: Poziția de start în vocea sursă (implicit 0).
    Output: Dicționar cu rezultatele.
    """
    if len(voices[source_voice]) < start_pos + length:
        return None  # Ignorăm dacă nu sunt suficiente note
    
    pattern_triplets = voices[source_voice][start_pos:start_pos + length]
    pattern_intervals = triplets_to_intervals(pattern_triplets)
    
    # Standardizăm intervalele pentru a obține o reprezentare unică
    pattern_intervals_tuple = standardize_pattern_intervals(pattern_intervals)
    
    # Verificăm dacă tiparul a fost deja procesat
    if pattern_intervals_tuple in checked_patterns:
        return None  # Dacă da, ignorăm procesarea acestuia
    
    # Adăugăm tiparul la setul de tipare verificate
    checked_patterns.add(pattern_intervals_tuple)
    
    total_matches = 0
    matches_by_voice = {}

    # Verificăm potrivirile în toate vocile
    for voice_name in voice_order[:]:
        intervals = triplets_to_intervals(voices[voice_name])
        matches = similarity_function(pattern_intervals, intervals)
        matches_by_voice[voice_name] = matches
        total_matches += len(matches)
    
    return {
        'source_voice': source_voice,
        'length': length,
        'start_pos': start_pos,
        'total_matches': total_matches,
        'pattern_notes': [pitch.Pitch(p).nameWithOctave for p, _, _ in pattern_triplets],
        'pattern_notes_midi': [p for p, _, _ in pattern_triplets],
        'pattern_intervals': [(delta_p, d) for delta_p, _, d in pattern_intervals],
        'matches_by_voice': matches_by_voice,
        'onset': voices[source_voice][start_pos][1] if pattern_triplets else None
    }

def save_results(results, voices, output_file, output_dir):
    """
    Salvează rezultatele într-un fișier JSON, fără grupare, incluzând patternul, numărul de potriviri
    și detaliile potrivirilor din voci, cu notele în MIDI, fără surse, doar pentru total_matches > 1.
    Input:
        - results: Lista de dicționare cu rezultatele pentru fiecare lungime, voce sursă și poziție.
        - voices: Dicționar cu vocile și tripletele lor.
        - output_file: Calea către fișierul JSON de ieșire.
    """
    json_data = []
    for result in results:
        if result is None or result['total_matches'] <= 1:
            continue
        
        # Procesăm potrivirile pentru fiecare voce
        processed_matches_by_voice = {}
        for voice_name, matches_list in result['matches_by_voice'].items():
            processed_matches = []
            for b, score in matches_list:
                L = result['length']
                first_note = max(0, b - (L - 1))
                last_note = min(len(voices[voice_name]) - 1, b)
                matched_notes_indices = range(first_note, last_note + 1)
                matched_notes_names = [pitch.Pitch(voices[voice_name][i][0]).nameWithOctave for i in matched_notes_indices]
                matched_notes_midi = [voices[voice_name][i][0] for i in matched_notes_indices]

                combined_notes = [
                    f"{pitch.Pitch(voices[voice_name][i][0]).nameWithOctave} ({voices[voice_name][i][0]})"
                    for i in matched_notes_indices
                ]
                onset = voices[voice_name][first_note][1] if matched_notes_indices else None
                processed_matches.append({
                    'onset': onset,
                    'matched_notes': combined_notes
                })
            processed_matches_by_voice[voice_name] = processed_matches
        
        # Construim intrarea pentru JSON
        output_entry = {
            'pattern': {
                'intervals (p2 - p1, duration)': ' '.join([f"({dp}, {dur})" for dp, dur in result['pattern_intervals']])
            },
            'total_matches': result['total_matches'],
            'matches': processed_matches_by_voice
        }
        json_data.append(output_entry)
    
    # Salvăm în fișier JSON
    with open(output_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"Rezultatele au fost salvate în {output_file}.")
    
    return json_data

def find_pattern(csv_file, output_dir):
    """
    Rulează algoritmul pentru diferite lungimi ale tiparului din toate pozițiile fiecărei voci,
    verificând vocile specificate, afișează doar cel mai bun tipar și salvează toate rezultatele în fișier JSON.
    """
    voices = load_triplets(csv_file)
    voice_order = ['Soprano', 'Alto', 'Tenor', 'Bass']  # Ordinea fixă a vocilor
    
    results = []
    for source_voice in voice_order:
        voice_length = len(voices[source_voice])
        for length in range(min_length, max_length + 1):
            # Iterăm peste toate pozițiile posibile pentru lungimea dată
            for start_pos in range(voice_length - length + 1):
                if len(voices[source_voice]) >= start_pos + length:
                    result = evaluate_pattern_length(voices, source_voice, length, voice_order, start_pos)
                    if result:
                        results.append(result)
    
    output_file = os.path.join(output_dir, "patterns.json")  # Fișierul unde salvăm rezultatele
    # Salvăm rezultatele fără grupare
    pattern_groups = save_results(results, voices, output_file, output_dir)