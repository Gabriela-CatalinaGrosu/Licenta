from music21 import *
import csv
import os

def durata_piesa(partitura):
    """
    Calculeaza durata piesei si o afiseaza.

    Args:
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.
    """
    tempo_markers = partitura.flat.getElementsByClass('MetronomeMark')

    # Dacă există un tempo definit, extrage BPM-ul
    if tempo_markers:
        bpm = tempo_markers[0].number

    quarter_length = partitura.flat.quarterLength
    if bpm is not None:
        # Calcularea duratei totale a piesei în secunde
        total_duration = partitura.duration.quarterLength  # Durata totală în "lungimi de cvartă"
        seconds_per_quarter = 60 / bpm  # Cât timp durează o cvartă de notă (în secunde)
        total_seconds = total_duration * seconds_per_quarter
        print(f"Timpul total al piesei este: {total_seconds:.2f} secunde")
        print(f"Timpul total al piesei este: {quarter_length:.2f} măsuri")
    else:
        print("Nu s-a găsit un tempo definit. Timpul nu poate fi calculat.")
        print(f"Timpul total al piesei este: {quarter_length:.2f} măsuri (fără tempo definit)")

def analiza_voce(part, output_dir):
    """
    Analizează un instrument (voce) dintr-o partitură și returnează datele notelor.

    Args:
        part (str): instrumentul (vocea) de analizat.
        output_dir (str): directorul unde se salveaza informatia.

    Return:
        tuplu (note_data (list), part_name (str)): notele corespunzătoare instrumentului/vocii, numele instrumentului/vocii
    """
    # Numele instrumentului sau fallback
    part_name = part.partName if part.partName else 'Unknown'
    # Lista pentru datele notelor
    note_data = []
    
    # Creează directorul de ieșire dacă nu există
    os.makedirs(output_dir, exist_ok=True)
    instrument_dir = os.path.join(output_dir, part_name)
    os.makedirs(instrument_dir, exist_ok=True)
    nume_fisier = os.path.join(instrument_dir, f"{part_name}_note.csv")

    # Verifică dacă fișierul CSV există deja
    if os.path.isfile(nume_fisier):
        print(f"Fișierul CSV '{nume_fisier}' există deja. Îl voi suprascrie.")
    else:
        print(f"Fișierul CSV '{nume_fisier}' nu există. Îl voi crea.")


    with open(nume_fisier, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['pitch', 'pitch_num', 'frequency', 'octave', 'duration', 'offset']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for element in part.recurse():
            if isinstance(element, note.Note):
                note_info = {
                    'pitch': str(element.pitch),
                    'pitch_num': int(element.pitch.midi),
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
                        'pitch_num': int(n.midi),
                        'frequency': n.frequency,
                        'octave': n.octave,
                        'duration': float(element.duration.quarterLength),
                        'offset': float(element.offset)
                    }
                    note_data.append(note_info)
                    writer.writerow(note_info)
    
    return note_data, part_name

def extrage_note_muzicale(partitura, name, output_dir, output_subdir = "note"):
    """
    Extrage notele muzicale dintr-un fișier MusicXML și le salvează în fișiere CSV.

    Args:
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.
        name (str): numele fisierului de intrare
        output_dir (str): directorul principal unde sunt salvate informatiile
        output_subdir (str): subdirectorul unde se salveaza segmentarea

    Return:
        output_file (str): calea către fișierul CSV cu notele extrase.
        output_dir (str): directorul unde sunt salvate notele.
    """

    # Creează directorul de ieșire dacă nu există
    os.makedirs(output_dir, exist_ok=True)
    output_dir = os.path.join(output_dir, output_subdir)
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{name}.csv")

    # Verifică dacă fișierul CSV există deja
    if os.path.isfile(output_file):
        print(f"Fișierul CSV '{output_file}' există deja. Îl voi suprascrie.")
    else:
        print(f"Fișierul CSV '{output_file}' nu există. Îl voi crea.")
        
    durata_piesa(partitura)
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
                        'pitch_num': int(element.pitch.midi),
                        'frequency': element.pitch.frequency,
                        'octave': element.octave,
                        'duration': float(element.duration.quarterLength),
                        'offset': float(element.offset)
                    })
                elif isinstance(element, chord.Chord):
                    for n in element.pitches:
                        note_data.append({
                            'pitch': str(n),
                            'pitch_num': int(n.midi),
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
            fieldnames = ['type', 'pitch', 'pitch_num', 'frequency', 'octave', 'duration', 'offset']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in all_notes:
                if item.get('type') == 'Instrument':
                    writer.writerow({'type': 'Instrument', 'pitch': item['value']})
                else:
                    writer.writerow({
                        'type': 'Note',
                        'pitch': item['pitch'],
                        'pitch_num': item['pitch_num'],
                        'frequency': item['frequency'],
                        'octave': item['octave'],
                        'duration': item['duration'],
                        'offset': item['offset']
                    })
        print(f"Notele au fost scrise în fișierul: '{output_file}'")
    except Exception as e:
        print(f"Eroare la scrierea în fișierul CSV '{output_file}': {e}")

    return output_file, output_dir
    
