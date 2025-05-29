import argparse
import os
from music21 import converter, instrument, note, chord, corpus
from note import *
from segmentare import *
from pattern import *


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


def main():
    """Procesează un fișier MusicXML sau MIDI și realizează analize muzicale."""
    parser = argparse.ArgumentParser(description="Analizează o piesă muzicală cu music21.")
    parser.add_argument(
        "input_file",
        type=str,
        help="Calea către fișierul de intrare (MusicXML .xml sau MIDI .mid)"
    )

    args = parser.parse_args()
    input_file = os.path.join("input", args.input_file)
    if not os.path.exists(input_file):
        print(f"Eroare: Fișierul {input_file} nu a fost creat!")
        return
    
    if not input_file.endswith(('.xml', '.mid', '.midi')):
        print("Eroare: Fișierul trebuie să fie în format MusicXML (.xml) sau MIDI (.mid, .midi)!")
        return
        
    try:
        # Încărcați fișierul
        partitura = converter.parse(input_file)
    except Exception as e:
        try:
            partitura = corpus.parse(input_file)
        except Exception as e:
            print(f"Eroare la încărcarea fișierului XML '{input_file}': {e}")
            return

    name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = os.path.join("output", name)
    os.makedirs(output_dir, exist_ok=True)
    extrage_note_muzicale(partitura, name, output_dir)
    segmentare(partitura, name, output_dir)

    
 
if __name__ == '__main__':
    main()
