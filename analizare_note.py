from music21 import *
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
from grafice import *

def analiza_distributie_pitch(note, instr, output_dir="analize"):
    """
    Analizează distribuția înălțimilor și salvează rezultatele + grafice.
    """
    # Distribuția pitch-urilor
    pitch_counts = note['pitch'].value_counts().reset_index()
    pitch_counts.columns = ['pitch', 'count']
    output_file = os.path.join(output_dir, f"pitch_distribution_{instr}.csv")
    pitch_counts.to_csv(output_file, index=False)
    print(f"Distribuția pitch-urilor ({instr}) salvată în: {output_file}")
    
    # Grafic
    grafic_distributie(instr, pitch_counts,  output_dir)
    
    # Statistici generale
    stats = {
        'numar_note': len(note),
        'pitch_uri_unice': len(note['pitch'].unique()),
        'octava_minima': note['octave'].min() if not note.empty else None,
        'octava_maxima': note['octave'].max() if not note.empty else None
    }
    stats_file = os.path.join(output_dir, f"pitch_stats_{instr}.txt")
    with open(stats_file, 'w', encoding='utf-8') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    print(f"Statistici pitch-uri ({instr}) salvate în: {stats_file}")


def analiza_ritm(note, instr, output_dir="analize"):
    """
    Analizează distribuția duratelor și salvează rezultatele + grafice.
    """
    
    # Distribuția duratelor
    duration_counts = note['duration'].value_counts().reset_index()
    duration_counts.columns = ['duration', 'count']
    output_file = os.path.join(output_dir, f"duration_distribution_{instr}.csv")
    duration_counts.to_csv(output_file, index=False)
    print(f"Distribuția duratelor ({instr}) salvată în: {output_file}")
    
    # Grafic toate vocile
    grafic_distributie_ritm(instr, duration_counts, output_dir)
    
    # Statistici ritmice
    stats = {
        'durata_medie': note['duration'].mean() if not note.empty else None,
        'durata_minima': note['duration'].min() if not note.empty else None,
        'durata_maxima': note['duration'].max() if not note.empty else None
    }
    stats_file = os.path.join(output_dir, f"rhythm_stats_{instr}.txt")
    with open(stats_file, 'w', encoding='utf-8') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    print(f"Statistici ritmice ({instr}) salvate în: {stats_file}")


def analiza_densitate(note, instr, output_dir="analize", bin_size=1.0):
    """
    Analizează densitatea notelor în timp și salvează rezultatele + grafice.
    """
    # Grupare pe intervale de timp
    note = note.copy()
    note['time_bin'] = (note['offset'] // bin_size) * bin_size
    density = note.groupby('time_bin').size().reset_index()
    density.columns = ['time_bin', 'count']
    output_file = os.path.join(output_dir, f"density_{instr}.csv")
    density.to_csv(output_file, index=False)
    print(f"Densitatea notelor ({instr}) salvată în: {output_file}")
    
    # Grafic
    grafic_densitate(instr, density, output_dir)


def analiza_file(csv_file, output_dir = "analize"):

    # Creează directorul de ieșire dacă nu există
    os.makedirs(output_dir, exist_ok=True)

    # Verifică dacă fișierul CSV există deja
    if not os.path.isfile(csv_file):
        print(f"Fișierul CSV '{csv_file}' nu există. Îl voi crea.")
        return
    else:
        file = pd.read_csv(csv_file)
        note = file[file['type'] == 'Note']
        analiza_distributie_pitch(note, "toate vocile", output_dir)
        analiza_ritm(note, "toate vocile", output_dir)
        analiza_densitate(note, "toate vocile", output_dir)

        # Distribuția pitch-urilor (toate vocile)
        instrumente = file[file['type'] == 'Instrument']['pitch'].unique()
        for instr in instrumente:
            file_instr = str(instr) + "_note.csv"
            note_instr = file[file['type'] == 'Note']
            analiza_distributie_pitch(note_instr, instr, output_dir)
            analiza_ritm(note_instr, instr, output_dir)
            analiza_densitate(note_instr, instr, output_dir)
