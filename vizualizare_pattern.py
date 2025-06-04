import json
import os
import matplotlib.pyplot as plt
import numpy as np

def extract_source_pattern(patterns):
    """
    Extrage pattern-ul care are cele mai multe match-uri egale cu sursa (intervale melodice identice).
    
    Args:
        patterns (list): Lista de patterns extrase din fișierul JSON.
        
    Returns:
        dict: Pattern-ul cu cele mai multe match-uri egale cu sursa.
    """
    max_equal_matches = 0
    best_pattern = None

    for pattern in patterns:
        source_intervals_str = pattern['pattern']['intervals (p2 - p1, duration)']
        source_intervals = [int(interval.split(',')[0].strip('(')) for interval in source_intervals_str.split(') ') if interval.strip()]
        s_num_notes = pattern['pattern']['num_notes']
        
        equal_matches_count = 0
        for _, matches in pattern['matches'].items():
            for match in matches:
                match_intervals_str = match['intervals (p2 - p1, duration)']
                match_intervals = [int(interval.split(',')[0].strip('(')) for interval in match_intervals_str.split(') ') if interval.strip()]
                if match['num_notes'] == s_num_notes and match_intervals == source_intervals:
                    equal_matches_count += 1
        
        if equal_matches_count > max_equal_matches:
            max_equal_matches = equal_matches_count
            best_pattern = pattern

    if best_pattern is None:
        raise ValueError("Nu s-au găsit match-uri egale cu sursa în niciun pattern.")

    return best_pattern


def extract_chousen_pattern(patterns, criterion):
    """
    Alege un pattern din lista de patterns pe baza unui criteriu specificat.
    Criteriul poate fi 'onset' pentru cel mai mic onset sau 'matches' pentru cel mai mare număr de potriviri.
    Dacă criteriul este 'sources', se extrage pattern-ul sursă cu cele mai multe potriviri.
    Args:
        patterns (list): Lista de patterns extrase din fișierul JSON.
        criterion (str): Criteriul de selecție ('onset', 'matches' sau 'sources').
        
    Returns:
        dict: Pattern-ul ales pe baza criteriului specificat.
    """

    if criterion == 'onset':
        chosen_pattern = min(patterns, key=lambda p: (p['pattern']['onset'], -p['total_matches']))
    elif criterion == 'matches':
        chosen_pattern = max(patterns, key=lambda p: (p['total_matches'], -p['pattern']['onset']))
    elif criterion == 'sources':
        chosen_pattern = extract_source_pattern(patterns)
    else:
        raise ValueError("Criteriul trebuie să fie 'onset' sau 'matches'.")

    return chosen_pattern

def extract_pattern(json_file, criterion):
    """
    Extrage un pattern sursă din patterns.json și organizează potrivirile ca Soursa, Match pe voci.
    S include potrivirile cu intervale melodice (p2 - p1) exact ca sursa, ignorând durata.
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

    chosen_pattern = extract_chousen_pattern(patterns, criterion)

    source_intervals_str = chosen_pattern['pattern']['intervals (p2 - p1, duration)']
    source_intervals = [int(interval.split(',')[0].strip('(')) for interval in source_intervals_str.split(') ') if interval.strip()]
    
    s_data = []
    s_onset = chosen_pattern['pattern']['onset']
    s_num_notes = chosen_pattern['pattern']['num_notes']
    s_end = s_onset + (s_num_notes - 1)
    s_voice = chosen_pattern['pattern']['source_voice']
    s_data.append((s_onset, s_end, s_voice))

    all_matches0 = []
    all_matches1 = []
    all_matches_1 = []
    all_matches2 = []
    all_matches_2 = []
    for voice, matches in chosen_pattern['matches'].items():
        for match in matches:
            onset = match['onset']
            num_notes = match['num_notes']
            end = onset + (num_notes - 1)
            match_intervals_str = match['intervals (p2 - p1, duration)']
            match_intervals = [int(interval.split(',')[0].strip('(')) for interval in match_intervals_str.split(') ') if interval.strip()]
            
            if num_notes == s_num_notes and match_intervals == source_intervals:
                s_data.append((onset, end, voice))
            else:
                dif_list = [x for x in match_intervals if x not in source_intervals]
                dif = sum(dif_list)
                dif /= (num_notes - 1)
                if dif == 0:
                    all_matches0.append((onset, end, voice))
                elif dif in [0, 0.5]:
                    all_matches1.append((onset, end, voice))
                elif dif > 0.5:
                    all_matches2.append((onset, end, voice))
                elif dif >= -0.5:
                    all_matches_1.append((onset, end, voice))
                elif dif < -0.5:
                    all_matches_2.append((onset, end, voice))


    s_data.sort(key=lambda x: x[0])
    all_matches0.sort(key=lambda x: x[0])
    all_matches1.sort(key=lambda x: x[0])
    all_matches2.sort(key=lambda x: x[0])
    all_matches_1.sort(key=lambda x: x[0])
    all_matches_2.sort(key=lambda x: x[0])

    #  facem un dictionar cu liestele de matches
    all_matches_dict = {
        'all_matches0': all_matches0,
        'all_matches1': all_matches1,
        'all_matches2': all_matches2,
        'all_matches_1': all_matches_1,
        'all_matches_2': all_matches_2
    }

    return s_data, all_matches_dict

def generate_graphic(json_file, total_duration, output_dir, s_data, matches, name):
    """
    Generează graficul bazat pe datele din patterns.json, cu etichetele structurale sub grafic.
    
    Args:
        json_file (str): fișierul patterns.json.
        total_duration (float): Durata totală a piesei (în bătăi).
        output_dir (str): Directorul de ieșire pentru grafic.
        s_data (list): Lista de date pentru sursa pattern-ului.
        matches (list): Lista de potriviri pentru pattern-ul sursă.
    """

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

    matches0 = matches['all_matches0']
    matches1 = matches['all_matches1']
    matches2 = matches['all_matches2']
    matches_1 = matches['all_matches_1']
    matches_2 = matches['all_matches_2']

    for onset, end, voice in matches0:
        y_pos = voice_to_y[voice]
        ax.barh(y_pos, end - onset, left=onset, height=0.8, color="#D8CBA7", edgecolor='black', linewidth=1)
        ax.text((onset + end) / 2, y_pos, 'Match0', ha='center', va='center', fontsize=8, color='black')

    for onset, end, voice in matches1:
        y_pos = voice_to_y[voice]
        ax.barh(y_pos, end - onset, left=onset, height=0.8, color="#E07E7E", edgecolor='black', linewidth=1)
        ax.text((onset + end) / 2, y_pos, 'Match1', ha='center', va='center', fontsize=8, color='black')

    for onset, end, voice in matches2:
        y_pos = voice_to_y[voice]
        ax.barh(y_pos, end - onset, left=onset, height=0.8, color="#B91717", edgecolor='black', linewidth=1)
        ax.text((onset + end) / 2, y_pos, 'Match2', ha='center', va='center', fontsize=8, color='black')

    for onset, end, voice in matches_1:
        y_pos = voice_to_y[voice]
        ax.barh(y_pos, end - onset, left=onset, height=0.8, color="#5752E2", edgecolor='black', linewidth=1)
        ax.text((onset + end) / 2, y_pos, 'Match3', ha='center', va='center', fontsize=8, color='black')

    for onset, end, voice in matches_2:
        y_pos = voice_to_y[voice]
        ax.barh(y_pos, end - onset, left=onset, height=0.8, color="#182480", edgecolor='black', linewidth=1)
        ax.text((onset + end) / 2, y_pos, 'Match4', ha='center', va='center', fontsize=8, color='black')

    for onset, end, voice in s_data + matches1 + matches2 + matches_1 + matches_2:
        y_pos = voice_to_y[voice] - 0.5
        ax.text(onset, y_pos, f'{onset:.1f}', va='top', ha='center', fontsize=8)
        ax.text(end, y_pos, f'{end:.1f}', va='top', ha='center', fontsize=8)

    # Adăugăm etichetele structurale sub grafic
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='gray', edgecolor='black', label='Sursa'),
        Patch(facecolor='#D8CBA7', edgecolor='black', label='Match fără creștere/scădere evidentă'),
        Patch(facecolor='#E07E7E', edgecolor='black', label='Match cu creștere ușoară'),
        Patch(facecolor='#B91717', edgecolor='black', label='Match cu creștere accentuată'),
        Patch(facecolor='#5752E2', edgecolor='black', label='Match cu scădere ușoară'),
        Patch(facecolor='#182480', edgecolor='black', label='Match cu scădere accentuată')
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=5, fontsize=8)

    ax.set_xlim(0, total_duration)
    ax.set_ylim(-4.3, 0.5)  # Extindem y pentru a include etichetele
    fig.tight_layout(rect=[0, 0.3, 1, 1])  # Creștem spațiul inferior
    os.makedirs(output_dir, exist_ok=True)
    fig.savefig(os.path.join(output_dir, name))
    plt.close(fig)

def generate_all_graphics(json_file, total_duration, output_dir):
    """
    Generează toate graficele necesare pentru analiza pattern-urilor.

    Args:
        json_file (str): Calea către fișierul patterns.json.
        total_duration (float): Durata totală a piesei (în bătăi).
        output_dir (str): Directorul de ieșire pentru grafice.
    """
    # Generează graficul pentru analiza pattern-urilor
    s_data, matches = extract_pattern(json_file, 'onset')
    generate_graphic(json_file, total_duration, output_dir, s_data, matches, 'pattern_min_onset.png')

    s_data, matches = extract_pattern(json_file, 'matches')
    generate_graphic(json_file, total_duration, output_dir, s_data, matches, 'pattern_max_matches.png')

    s_data, matches = extract_pattern(json_file, 'sources')
    generate_graphic(json_file, total_duration, output_dir, s_data, matches, 'pattern_max_sources.png')
