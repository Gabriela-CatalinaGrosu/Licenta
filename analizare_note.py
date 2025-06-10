from music21 import *
import os
import pandas as pd
from grafice import *

def analiza_distributie_pitch(note, instr, output_dir="analize"):
    """
    Analizează distribuția înălțimilor și salvează rezultatele + grafice.

    Args:
        note (pd.DataFrame): notele piesei
        instr (str): vocea curentă
        output_dir (str): directorul unde se salvează fișierele
    """
    # Distribuția pitch-urilor
    pitch_counts = note['pitch'].value_counts().reset_index()
    pitch_counts.columns = ['pitch', 'count']

    instrument_dir = os.path.join(output_dir, instr)
    os.makedirs(instrument_dir, exist_ok=True)
    output_file = os.path.join(instrument_dir, f"distribuție_pitch_{instr}.csv")
    pitch_counts.to_csv(output_file, index=False)
    print(f"Distribuția pitch-urilor ({instr}) salvată în: {instrument_dir}")
    
    # Grafic
    grafic_distributie(instr, pitch_counts,  instrument_dir)
    
    # Statistici generale
    stats = {
        'numar_note': len(note),
        'pitch_uri_unice': len(note['pitch'].unique()),
        'octava_minima': note['octave'].min() if not note.empty else None,
        'octava_maxima': note['octave'].max() if not note.empty else None
    }
    stats_file = os.path.join(instrument_dir, f"pitch_{instr}.txt")
    with open(stats_file, 'w', encoding='utf-8') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    print(f"Statistici pitch-uri ({instr}) salvate în: {stats_file}")


def analiza_ritm(note, instr, output_dir="analize"):
    """
    Analizează distribuția duratelor și salvează rezultatele + grafice.

    Args:
        note (pd.DataFrame): notele piesei
        instr (str): vocea curentă
        output_dir (str): directorul unde se salvează fișierele
    """
    
    # Distribuția duratelor
    duration_counts = note['duration'].value_counts().reset_index()
    duration_counts.columns = ['duration', 'count']

    instrument_dir = os.path.join(output_dir, instr)
    os.makedirs(instrument_dir, exist_ok=True)
    output_file = os.path.join(instrument_dir, f"distribuție_durată_{instr}.csv")
    duration_counts.to_csv(output_file, index=False)
    print(f"Distribuția duratelor ({instr}) salvată în: {instrument_dir}")
    
    # Grafic toate vocile
    grafic_distributie_ritm(instr, duration_counts, instrument_dir)
    
    # Statistici ritmice
    stats = {
        'durata_medie': note['duration'].mean() if not note.empty else None,
        'durata_minima': note['duration'].min() if not note.empty else None,
        'durata_maxima': note['duration'].max() if not note.empty else None,
        'durata_totala': note['duration'].sum() if not note.empty else None
    }
    stats_file = os.path.join(instrument_dir, f"ritm_{instr}.txt")
    with open(stats_file, 'w', encoding='utf-8') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    print(f"Statistici ritmice ({instr}) salvate în: {stats_file}")


def analiza_densitate(note, instr, output_dir="analize", bin_size=1.0):
    """
    Analizează densitatea notelor în timp și salvează rezultatele + grafice.

    Args:
        note (pd.DataFrame): notele piesei
        instr (str): vocea curentă
        output_dir (str): directorul unde se salvează fișierele
        bin_size (float): dimensiunea bin-ului pentru analiza densității

    """
    # Grupare pe intervale de timp
    note = note.copy()
    note['time_bin'] = (note['offset'] // bin_size) * bin_size
    density = note.groupby('time_bin').size().reset_index()
    density.columns = ['time_bin', 'count']

    instrument_dir = os.path.join(output_dir, instr)
    os.makedirs(instrument_dir, exist_ok=True)
    output_file = os.path.join(instrument_dir, f"densitate_{instr}.csv")
    density.to_csv(output_file, index=False)
    print(f"Densitatea notelor ({instr}) salvată în: {output_file}")
    
    # Grafic
    grafic_densitate(instr, density, instrument_dir)


def analiza_note(csv_file, output_dir, output_subdir = "analiza_note"):
    """
    Functia principala pentru a analiza notele din partitura.

    Args:
        csv_file (str): fisierul de intrare CSV
        output_dir (str): directorul de iesire pentru analize
        output_subdir (str): subdirectorul unde se salveaza analizele

    Return:
        output_dir (str): directorul unde sunt salvate analizele
    """
   # Setează directorul de intrare pentru instrumente
    note_dir = os.path.join(os.path.dirname(csv_file))
    print(f"Director de intrare (note): {note_dir}")
    print(f"Director de ieșire (output): {os.path.join(output_dir, output_subdir)}")

    # Creează directorul de ieșire dacă nu există
    os.makedirs(os.path.join(output_dir, output_subdir), exist_ok=True)

    # Analiza pentru toate vocile (folosind fișierul principal)
    if not os.path.isfile(csv_file):
        print(f"Fișierul CSV '{csv_file}' nu există. Îl voi crea.")
        return output_dir
    else:
        file = pd.read_csv(csv_file)
        note = file[file['type'] == 'Note']
        analiza_distributie_pitch(note, "toate vocile", os.path.join(output_dir, output_subdir))
        analiza_ritm(note, "toate vocile", os.path.join(output_dir, output_subdir))
        analiza_densitate(note, "toate vocile", os.path.join(output_dir, output_subdir))

        # Instrumente
        instrumente = ['Soprano', 'Alto', 'Tenor', 'Bass']

        for instr in instrumente:
            file_instr = os.path.join(note_dir, instr, f"{instr}_note.csv")
            print(file_instr)
            if os.path.isfile(file_instr):
                note_instr = pd.read_csv(file_instr)
                analiza_distributie_pitch(note_instr, instr, os.path.join(output_dir, output_subdir))
                analiza_ritm(note_instr, instr, os.path.join(output_dir, output_subdir))
                analiza_densitate(note_instr, instr, os.path.join(output_dir, output_subdir))
            else:
                print(f"Fișierul '{file_instr}' nu există. Se omite analiza pentru {instr}.")

    return os.path.join(output_dir, output_subdir)