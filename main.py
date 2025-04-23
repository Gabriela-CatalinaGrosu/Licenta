import argparse
import os
from music21 import converter, instrument, note, chord, corpus
from note import *
from Licenta.note import *
from Licenta.segmentare import *
from Licenta.convers_input import *

def main():
    """Procesează un fișier MusicXML sau MIDI și realizează analize muzicale."""
    parser = argparse.ArgumentParser(description="Analizează o piesă muzicală cu music21.")
    parser.add_argument(
        "input_file",
        type=str,
        help="Calea către fișierul de intrare (MusicXML .xml sau MIDI .mid)"
    )

    args = parser.parse_args()
    input_file = args.input_file
    if input_file.endswith(('.mp3', '.wav')):
        input_file_midi = os.path.splitext(input_file)[0] + ".mid"
        input_file = convert_audio_to_midi(input_file, input_file_midi)
        if not os.path.exists(input_file):
            print(f"Eroare: Fișierul {input_file} nu a fost creat!")
            return
    elif not input_file.endswith(('.xml', '.mid', '.midi')):
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


    # output_file = os.path.basename(input_file).replace('.xml', '.csv')
    # numele fara extenstia fisierului
    name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = "analize"
    extrage_note_muzicale(partitura, name)
    # # # segmentare(output_file)
    # segmentare_tonalitate(partitura, name)
    # segmentare_acorduri(partitura, name)

    
 
if __name__ == '__main__':
    main()

