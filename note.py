from music21 import *
import csv
import os

from Licenta.analizare_note import *

def analiza_voce(part, output_dir):
    """
    Analizează un instrument dintr-o partitură și returnează datele notelor.
    """
    # Numele instrumentului sau fallback
    part_name = part.partName if part.partName else 'Unknown'
    # Lista pentru datele notelor
    note_data = []
    
    # Creează directorul de ieșire dacă nu există
    os.makedirs(output_dir, exist_ok=True)
    nume_fisier = os.path.join(output_dir, f"{part_name}_note.csv")

    # Verifică dacă fișierul CSV există deja
    if os.path.isfile(nume_fisier):
        print(f"Fișierul CSV '{nume_fisier}' există deja. Îl voi suprascrie.")
    else:
        print(f"Fișierul CSV '{nume_fisier}' nu există. Îl voi crea.")


    with open(nume_fisier, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['pitch', 'frequency', 'octave', 'duration', 'offset']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for element in part.recurse():
            if isinstance(element, note.Note):
                note_info = {
                    'pitch': str(element.pitch),
                    'frequency': element.pitch.frequency,
                    'octave': element.octave,
                    'duration': float(element.duration.quarterLength),
                    'offset': float(element.offset)
                }
                note_data.append(note_info)
                writer.writerow(note_info)
            elif isinstance(element, chord.Chord):
                for n in element.pitches:
                    note_info = {
                        'pitch': str(n),
                        'frequency': n.frequency,
                        'octave': n.octave,
                        'duration': float(element.duration.quarterLength),
                        'offset': float(element.offset)
                    }
                    note_data.append(note_info)
                    writer.writerow(note_info)
    
    return note_data, part_name

def extrage_note_muzicale(partitura, name, output_dir = "analiza_note"):
    """
    Extrage notele muzicale dintr-un fișier MusicXML și le salvează în fișiere CSV.
    """

    # Creează directorul de ieșire dacă nu există
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"{name}.csv")

    # Verifică dacă fișierul CSV există deja
    if os.path.isfile(output_file):
        print(f"Fișierul CSV '{output_file}' există deja. Îl voi suprascrie.")
    else:
        print(f"Fișierul CSV '{output_file}' nu există. Îl voi crea.")
        # cream fișierul CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['type', 'pitch', 'frequency', 'octave', 'duration', 'offset']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            # writer.writerow({'type': 'Instrument', 'pitch': 'Unknown'})
    # Încercăm să încărcăm fișierul XML folosind converter

    all_notes = []
    
    try:
        parts = instrument.partitionByInstrument(partitura)
        if parts:
            for part in parts:
                part_name = part.partName if part.partName else 'Unknown'
                print(f"Analizând partitura: {part_name}")
                # Analizează instrumentul și obține notele
                note_data, name = analiza_voce(part, output_dir)
                all_notes.append({'type': 'Instrument', 'value': name})
                all_notes.extend(note_data)
        else:
            print("Partitura nu conține informații despre voci separate. Analizând ca un singur flux.")
            note_data = []
            for element in partitura.recurse():
                if isinstance(element, note.Note):
                    note_data.append({
                        'pitch': str(element.pitch),
                        'frequency': element.pitch.frequency,
                        'octave': element.octave,
                        'duration': float(element.duration.quarterLength),
                        'offset': float(element.offset)
                    })
                elif isinstance(element, chord.Chord):
                    for n in element.pitches:
                        note_data.append({
                            'pitch': str(n),
                            'frequency': n.frequency,
                            'octave': n.octave,
                            'duration': float(element.duration.quarterLength),
                            'offset': float(element.offset)
                        })
            all_notes.extend(note_data)
    except Exception as e:
        print(f"Eroare la extragerea notelor: {e}")
        return

    try:
        # Salvează toate notele în fișierul CSV principal
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['type', 'pitch', 'frequency', 'octave', 'duration', 'offset']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in all_notes:
                if item.get('type') == 'Instrument':
                    writer.writerow({'type': 'Instrument', 'pitch': item['value']})
                else:
                    writer.writerow({
                        'type': 'Note',
                        'pitch': item['pitch'],
                        'frequency': item['frequency'],
                        'octave': item['octave'],
                        'duration': item['duration'],
                        'offset': item['offset']
                    })
        print(f"Notele au fost scrise în fișierul: '{output_file}'")
    except Exception as e:
        print(f"Eroare la scrierea în fișierul CSV '{output_file}': {e}")
    analiza_densitate(output_file, output_dir)
    analiza_ritm(output_file, output_dir)
    analiza_distributie_pitch(output_file, output_dir)