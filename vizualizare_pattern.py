import json
import os
import matplotlib.pyplot as plt
import numpy as np

def extract_pattern(json_file, criterion='onset'):
    """
    Extrage un pattern sursă din patterns.json și organizează potrivirile ca S, CS1, CS2 pe voci.
    S include potrivirile cu intervale melodice (p2 - p1) exact ca sursa, ignorând durata.
    Restul sunt împărțite între CS1 și CS2, separate pe voci.
    Păstrează toate potrivirile, inclusiv cele suprapuse în aceeași voce.
    
    Args:
        json_file (str): Calea către fișierul patterns.json.
        criterion (str): Criteriul de selecție ('onset' sau 'matches').
    
    Returns:
        tuple: (s_data, all_matches), unde fiecare este o listă de tupluri (onset, end, voice).
    """
    with open(json_file, 'r') as f:
        patterns = json.load(f)

    if not patterns:
        raise ValueError("Fișierul patterns.json este gol.")

    if criterion == 'onset':
        chosen_pattern = min(patterns, key=lambda p: (p['pattern']['onset'], -p['total_matches']))
    elif criterion == 'matches':
        chosen_pattern = max(patterns, key=lambda p: (p['total_matches'], -p['pattern']['onset']))
    else:
        raise ValueError("Criteriul trebuie să fie 'onset' sau 'matches'.")

    source_intervals_str = chosen_pattern['pattern']['intervals (p2 - p1, duration)']
    source_intervals = [int(interval.split(',')[0].strip('(')) for interval in source_intervals_str.split(') ') if interval.strip()]
    
    s_data = []
    s_onset = chosen_pattern['pattern']['onset']
    s_num_notes = chosen_pattern['pattern']['num_notes']
    s_end = s_onset + (s_num_notes - 1)
    s_voice = chosen_pattern['pattern']['source_voice']
    s_data.append((s_onset, s_end, s_voice))

    all_matches = []
    for voice, matches in chosen_pattern['matches'].items():
        for match in matches:
            onset = match['onset']
            num_notes = match['num_notes']
            end = onset + (num_notes - 1)
            match_intervals_str = match['intervals (p2 - p1, duration)']
            match_intervals = [int(interval.split(',')[0].strip('(')) for interval in match_intervals_str.split(') ') if interval.strip()]
            
            if num_notes == s_num_notes and match_intervals == source_intervals:
                # if voice == s_voice and abs(onset - s_onset) < 1e-6:
                #     continue
                s_data.append((onset, end, voice))
            else:
                all_matches.append((onset, end, voice))

    s_data.sort(key=lambda x: x[0])
    all_matches.sort(key=lambda x: x[0])

    return s_data, all_matches

def generate_graphic(json_file, total_duration, output_dir):
    """
    Generează graficul bazat pe datele din patterns.json, cu etichetele structurale sub grafic.
    
    Args:
        json_file (str): fișierul patterns.json.
        total_duration (float): Durata totală a piesei (în bătăi).
        output_dir (str): Directorul de ieșire pentru grafic.
    """

    s_data, matches = extract_pattern(json_file, criterion='onset')

    fig, ax = plt.subplots(figsize=(12, 5))  # Creștem înălțimea figurii
    ax.set_title('Analiza pattern', fontsize=12, pad=10)
    ax.set_yticks([-3.6, -2.4, -1.2, 0])
    ax.set_yticklabels(['Bass', 'Tenor', 'Alto', 'Soprano'], fontsize=10)
    ax.set_ylabel('', fontsize=10)
    ax.set_xlabel('Timp (quarterLength)', fontsize=10)
    ax.set_xticks(np.arange(0, total_duration, 1))
    ax.set_xticklabels([str(i) for i in range(0, total_duration)], fontsize=8)
    ax.grid(True, axis='x', linestyle='--', alpha=0.3, linewidth=0.5)

    voice_to_y = {'Soprano': 0, 'Alto': -1.2, 'Tenor': -2.4, 'Bass': -3.6}

    for onset, end, voice in s_data:
        y_pos = voice_to_y[voice]
        ax.barh(y_pos, end - onset, left=onset, height=0.8, color='gray', edgecolor='black', linewidth=1)
        ax.text((onset + end) / 2, y_pos, 'Sursa', ha='center', va='center', fontsize=8, color='black')

    for onset, end, voice in matches:
        y_pos = voice_to_y[voice]
        ax.barh(y_pos, end - onset, left=onset, height=0.8, color='gray', edgecolor='black', linewidth=1)
        ax.text((onset + end) / 2, y_pos, 'Match', ha='center', va='center', fontsize=8, color='black')

    for onset, end, voice in s_data + matches:
        y_pos = voice_to_y[voice] - 0.5
        ax.text(onset, y_pos, f'{onset:.1f}', va='top', ha='center', fontsize=8)
        ax.text(end, y_pos, f'{end:.1f}', va='top', ha='center', fontsize=8)

    ax.set_xlim(0, total_duration)
    ax.set_ylim(-4.3, 0.5)  # Extindem y pentru a include etichetele
    fig.tight_layout(rect=[0, 0.3, 1, 1])  # Creștem spațiul inferior
    os.makedirs(output_dir, exist_ok=True)
    fig.savefig(os.path.join(output_dir, 'computed_analysis_voices.png'))
    plt.close(fig)