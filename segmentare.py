import csv
import os
from music21 import *

def analizare_tonalitate(partitura):
    """
    Segmentează o partitură în funcție de tonalitate.
    Args:
        partitura: Obiect music21 Score, partitura de analizat.
    Returns:
        segmente: O listă de tuple (tonalitate, start_time, end_time).
    """

    segmente = []
    masura_curenta = []
    tonalitate_curenta = None

    for masura in partitura.parts[0].getElementsByClass('Measure'):
        try:
            analiza_tonalitate = masura.analyze('key')
        except:
            # Dacă analiza eșuează, continuăm cu tonalitatea curentă
            analiza_tonalitate = tonalitate_curenta if tonalitate_curenta else key.Key('C')

        # Verifică dacă tonalitatea s-a schimbat
        if analiza_tonalitate != tonalitate_curenta and masura_curenta:
            start_time = masura_curenta[0].offset
            ultima_masura = masura_curenta[-1]
            end_time = ultima_masura.offset + ultima_masura.duration.quarterLength
            segmente.append((tonalitate_curenta, start_time, end_time))
            masura_curenta = [masura]
            tonalitate_curenta = analiza_tonalitate
        else:
            masura_curenta.append(masura)
            tonalitate_curenta = analiza_tonalitate

    # Adaugă ultimul segment
    if masura_curenta:
        start_time = masura_curenta[0].offset
        ultima_masura = masura_curenta[-1]
        end_time = ultima_masura.offset + ultima_masura.duration.quarterLength
        segmente.append((tonalitate_curenta, start_time, end_time))
    return segmente

def segmentare_tonalitate(partitura, name, output_dir="segmentare"):
    """
    Segmentează o partitură bazată pe tonalitate, salvând rezultatele într-un fișier.
    Args:
        partitura: Obiect music21 Score, partitura de analizat.
        name: Numele fișierului de ieșire.
        output_dir: Directorul în care se salvează fișierul.
    """
    output_file = os.path.join(output_dir, f'{name}_tonalitate.csv')
    dir = os.path.join(output_dir, 'tonalitate')
    # Creează directorul de ieșire pentru tonalitate dacă nu există
    os.makedirs(dir, exist_ok=True)

    output_file = os.path.join(dir, f'{name}tonalitate.csv')
    # Verifică dacă fișierul există
    if os.path.isfile(output_file):
        print(f"\tFișierul '{output_file}' există deja. Îl voi suprascrie.")
    else:
        print(f"\tFișierul '{output_file}' nu există. Îl voi crea.")
    
    segmente = analizare_tonalitate(partitura)

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['start', 'end', 'segment_name'])

            for idx, (tonalitate, start, end) in enumerate(segmente, 1):
                tonalitate_str = str(tonalitate).replace(' ', '_') if tonalitate else 'Unknown'
                writer.writerow([f"{start:.3f}", f"{end:.3f}", f"Seg#{idx}_Tonalitate_{tonalitate_str}"])

        print(f"\tRezultatele au fost salvate în fișierul: '{output_file}'")
    except Exception as e:
        print(f"Eroare la scrierea în fișierul CSV: {e}")

    

def repetitii(partitura):
    """
    Segmentează o partitură bazată pe repetiții melodice, salvând rezultatele într-un fișier.

    Args:
        partitura: Obiect music21 Score, partitura de analizat.
    """
    print("\tRealizez segmentarea bazată pe repetiții melodice...")
    
    # Colectează note și acorduri
    note_si_acorduri = partitura.recurse().getElementsByClass((note.Note, chord.Chord))
    if not note_si_acorduri:
        print("\tEroare: Partitura nu conține note sau acorduri!")
        return

    segmente = []
    fraze = []
    lungime_fraza = 8

    # Iterează prin fraze cu suprapunere minimă
    for i in range(0, len(note_si_acorduri) - lungime_fraza + 1, lungime_fraza // 2):
        fraza = note_si_acorduri[i:i + lungime_fraza]
        if len(fraza) < lungime_fraza:
            continue

        # Extrage înălțimile (pitches) MIDI
        pitches = []
        for elem in fraza:
            try:
                if isinstance(elem, note.Note):
                    pitches.append(elem.pitch.midi)
                elif isinstance(elem, chord.Chord):
                    if elem.pitches:  # Verifică dacă acordul are înălțimi
                        pitches.extend(p.midi for p in elem.pitches)
            except:
                continue  # Ignoră elementele invalide

        if not pitches:
            continue  # Ignoră frazele fără înălțimi valide

        # Calculează timpii
        start_time = fraza[0].offset
        end_time = fraza[-1].offset + fraza[-1].duration.quarterLength
        if end_time <= start_time:
            continue  # Ignoră segmentele invalide

        # Caută fraza în lista existentă
        fraza_gasita = False
        for idx, fraza_veche in enumerate(fraze):
            if pitches == fraza_veche['pitches']:
                # Adaugă segment doar dacă nu e duplicat
                if not any(abs(start_time - s[1]) < 0.01 and abs(end_time - s[2]) < 0.01 for s in segmente):
                    segmente.append((idx, start_time, end_time))
                fraza_gasita = True
                break

        if not fraza_gasita:
            fraze.append({'pitches': pitches})
            segmente.append((len(fraze) - 1, start_time, end_time))

    # Adaugă segmente rămase, dacă există
    if len(note_si_acorduri) > 0 and segmente and segmente[-1][2] < note_si_acorduri[-1].offset:
        start_time = segmente[-1][2]
        end_time = note_si_acorduri[-1].offset + note_si_acorduri[-1].duration.quarterLength
        segmente.append((len(fraze), start_time, end_time))

    # Sortează segmentele după timpul de început
    segmente.sort(key=lambda x: x[1])
    return segmente

    

def segmentare_repetitii(partitura, name, output_dir="segmentare"):
    # Creează directorul de ieșire dacă nu există
    os.makedirs(output_dir, exist_ok=True)
    dir = os.path.join(output_dir, 'repetitii')
    # Creează directorul de ieșire pentru repetitii dacă nu există
    os.makedirs(dir, exist_ok=True)
    output_file = os.path.join(dir, f'{name}_repetitii.csv')
    # Verifică dacă fișierul există
    if os.path.isfile(output_file):
        print(f"\tFișierul '{output_file}' există deja. Îl voi suprascrie.")
    else:
        print(f"\tFișierul '{output_file}' nu există. Îl voi crea.")
    
    segmente = repetitii(partitura)

    # Salvează rezultatele
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['start', 'end', 'segment_name'])
            for idx, (fraza_idx, start, end) in enumerate(segmente, 1):
                writer.writerow([f"{start:.3f}", f"{end:.3f}", f"Seg#{idx}_Repetitie_{fraza_idx}"])
        
        print(f"\tRezultatele au fost salvate în fișierul: '{output_file}'")
    except Exception as e:
        print(f"\tEroare la scrierea fișierului: {e}")



    
def acorduri(partitura):
    """
    Segmentează o partitură bazată pe acorduri, salvând rezultatele într-un fișier.

    Args:
        partitura: Obiect music21 Score, partitura de analizat.
    """
    print("\tRealizez segmentarea bazată pe acorduri...")

# Colectează acordurile din partitură
    acorduri = partitura.recurse().getElementsByClass('Chord')
    segmente = []

    # Dacă există acorduri, creează segmente bazate pe ele
    if acorduri:
        for acord in acorduri:
            try:
                # Identifică figura acordului (ex. C, G7, Am)
                figura = acord.figure
                # Considerăm doar acorduri semnificative (majore, minore, septime, diminuate)
                if (acord.isMajorTriad() or 
                    acord.isMinorTriad() or 
                    acord.isDominantSeventh() or 
                    acord.isDiminishedSeventh()):
                    start_time = acord.offset
                    end_time = acord.offset + acord.duration.quarterLength
                    if end_time > start_time:  # Ignoră segmentele de lungime zero
                        segmente.append((figura, start_time, end_time))
            except:
                continue  # Ignoră acordurile invalide
    else:
        # Fallback: Dacă nu există acorduri, folosim notele
        print("\tNu s-au găsit acorduri. Folosesc notele ca fallback...")
        note_si_acorduri = partitura.recurse().getElementsByClass((note.Note, chord.Chord))
        for elem in note_si_acorduri:
            start_time = elem.offset
            end_time = elem.offset + elem.duration.quarterLength
            if end_time > start_time:
                # Pentru note, folosim pitch-ul ca "figura"
                figura = elem.pitch.nameWithOctave if isinstance(elem, note.Note) else "Unknown"
                segmente.append((figura, start_time, end_time))

    # Dacă nu s-au găsit segmente valide, avertizează
    if not segmente:
        print("\tEroare: Nu s-au găsit acorduri sau note valide pentru segmentare!")
        return

    # Sortează segmentele după timpul de început
    segmente.sort(key=lambda x: x[1])
    return segmente


def segmentare_acorduri(partitura, name, output_dir="segmentare"):
    # Creează directorul de ieșire dacă nu există
    os.makedirs(output_dir, exist_ok=True)

    dir = os.path.join(output_dir, 'acorduri')
    # Creează directorul de ieșire pentru acorduri dacă nu există
    os.makedirs(dir, exist_ok=True)
    # Numele fișierului de ieșire
    output_file = os.path.join(dir, f'{name}_acorduri.csv')
    # Verifică dacă fișierul există
    if os.path.isfile(output_file):
        print(f"\tFișierul '{output_file}' există deja. Îl voi suprascrie.")
    else:
        print(f"\tFișierul '{output_file}' nu există. Îl voi crea.")

    segmente = acorduri(partitura)
    # Salvează rezultatele
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['start', 'end', 'segment_name'])
            for idx, (figura, start, end) in enumerate(segmente, 1):
                figura_str = figura.replace(' ', '_') if figura else 'Unknown'
                writer.writerow([f"{start:.3f}", f"{end:.3f}", f"Seg#{idx}_Acord_{figura_str}"])
        print(f"\tRezultatele au fost salvate în fișierul: '{dir}'")
    except Exception as e:
        print(f"\tEroare la scrierea fișierului: {e}") 


def segmentare(partitura, name, output_dir, output_subdir="segmentare"):
    """
    Funcția principală pentru segmentarea partiturii.
    Apelează funcțiile de segmentare bazate pe tonalitate și acorduri.
    """
    print(f"\tRealizez segmentarea partiturii '{name}'...")
    
    # Creează directorul de ieșire dacă nu există
    os.makedirs(output_dir, exist_ok=True)
    output_dir = os.path.join(output_dir, output_subdir)
    os.makedirs(output_dir, exist_ok=True)

    # Segmentare bazată pe tonalitate
    segmentare_tonalitate(partitura, name, output_dir)

    # Segmentare bazată pe acorduri
    segmentare_acorduri(partitura, name, output_dir)

    # Segmentare bazată pe repetiții
    segmentare_repetitii(partitura, name, output_dir)
