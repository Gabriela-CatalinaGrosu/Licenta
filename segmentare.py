import csv
import os
import matplotlib.pyplot as plt
from music21 import *

def analizare_tonalitate(partitura):
    """
    Segmentează o partitură în funcție de tonalitate.

    Args:
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.

    Returns:
        list: Lista de segmente de tonalitate, fiecare segment fiind un tuplu (tonalitate, start, end).
    """
    segmente = []
    masura_curenta = []
    tonalitate_curenta = None

    durata_totala = partitura.duration.quarterLength

    for masura in partitura.parts[0].getElementsByClass('Measure'):
        try:
            analiza_tonalitate = masura.analyze('key')
        except:
            analiza_tonalitate = tonalitate_curenta if tonalitate_curenta else key.Key('C')

        if analiza_tonalitate != tonalitate_curenta and masura_curenta:
            start_time = masura_curenta[0].offset
            ultima_masura = masura_curenta[-1]
            end_time = ultima_masura.offset + ultima_masura.duration.quarterLength
            # Limităm end_time la durata totală a partiturii
            end_time = min(end_time, durata_totala)
            segmente.append((tonalitate_curenta, start_time, end_time))
            masura_curenta = [masura]
            tonalitate_curenta = analiza_tonalitate
        else:
            masura_curenta.append(masura)
            tonalitate_curenta = analiza_tonalitate

    if masura_curenta:
        start_time = masura_curenta[0].offset
        ultima_masura = masura_curenta[-1]
        end_time = ultima_masura.offset + ultima_masura.duration.quarterLength
        # Limităm end_time la durata totală a partiturii
        end_time = min(end_time, durata_totala)
        segmente.append((tonalitate_curenta, start_time, end_time))
    return segmente

def segmentare_tonalitate(partitura, output_dir):
    """
    Segmentează o partitură bazată pe tonalitate, salvând rezultatele într-un fișier.

    Args:
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.
        output_dir (str): directorul unde sunt salvate informațiile (output_dir/output_subdir).

    Returns:
        list: Lista de segmente de tonalitate, fiecare segment fiind un tuplu (tonalitate, start, end).
    """
    dir = os.path.join(output_dir, 'tonalitate')
    os.makedirs(dir, exist_ok=True)
    output_file = os.path.join(dir, 'tonalitate.csv')

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
                writer.writerow([f"{start:.3f}", f"{end:.3f}", f"Secțiunea {idx}: {tonalitate_str}"])
        print(f"\tRezultatele au fost salvate în fișierul: '{output_file}'")
    except Exception as e:
        print(f"Eroare la scrierea în fișierul CSV: {e}")

    return segmente

def acorduri(partitura):
    """
    Segmentează o partitură bazată pe acorduri, combinând notele simultane din toate vocile.

    Args:
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.
    
    Returns:
        list: Lista de segmente de acorduri, fiecare segment fiind un tuplu (figura, start, end).
    """
    print("\tRealizez segmentarea bazată pe acorduri...")
    segmente = []
    
    # Colectăm toate notele din toate părțile
    note_toate = []
    for part in partitura.parts:
        for n in part.recurse().getElementsByClass('Note'):
            note_toate.append((n.offset, n.offset + n.duration.quarterLength, n.pitch, part))

    note_toate.sort(key=lambda x: (x[0], x[1]))

    if not note_toate:
        print("\tEroare: Nu s-au găsit note în partitură!")
        return []

    # Grupăm notele simultane pentru a forma acorduri
    i = 0
    while i < len(note_toate):
        start_time = note_toate[i][0]
        end_time = note_toate[i][1]
        pitches = [note_toate[i][2]]
        
        # Cautăm note care încep aproape simultan (toleranță mărită la 0.1)
        j = i + 1
        while j < len(note_toate) and abs(note_toate[j][0] - start_time) < 0.1:
            pitches.append(note_toate[j][2])
            end_time = min(end_time, note_toate[j][1])
            j += 1

        # Creăm un acord din notele simultane
        try:
            acord = chord.Chord(pitches)
            acord.duration = duration.Duration(end_time - start_time)
            # Relaxăm condițiile: acceptăm acorduri cu cel puțin 3 note
            if len(pitches) >= 3 and (end_time - start_time) >= 0.25:
                simbol = acord.pitchedCommonName  # Ex. "C major"
                segmente.append((simbol, start_time, end_time))
                print(f"\tAcord detectat: {simbol} de la {start_time} la {end_time}")
            else:
                print(f"\tAcord ignorat (prea puține note sau durată scurtă): {pitches}")
        except Exception as e:
            print(f"\tEroare la crearea acordului: {e}, pitches: {pitches}")

        i = j

    if not segmente:
        print("\tEroare: Nu s-au găsit acorduri semnificative!")
        # Fallback: Încercăm analiza armonică
        print("\tÎncercăm analiza armonică ca fallback...")
        try:
            roman = partitura.analyze('roman')
            for event in roman.recurse().getElementsByClass('RomanNumeral'):
                start_time = event.offset
                end_time = start_time + event.duration.quarterLength
                if end_time - start_time >= 0.25:
                    segmente.append((event.figure, start_time, end_time))
                    print(f"\tAcord roman detectat: {event.figure} de la {start_time} la {end_time}")
        except Exception as e:
            print(f"\tEroare la analiza armonică: {e}")

    if not segmente:
        print("\tEroare finală: Tot nu s-au găsit acorduri!")
        return []

    segmente.sort(key=lambda x: x[1])
    print(f"\tSegmente acorduri detectate: {segmente}")
    return segmente

def segmentare_acorduri(partitura, output_dir):
    """
    Segmentează o partitură bazată pe acorduri, salvând rezultatele într-un fișier.

    Args:
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.
        output_dir (str): directorul unde sunt salvate informațiile (output_dir/output_subdir).

    Returns:
        list: Lista de segmente de acorduri, fiecare segment fiind un tuplu (figura, start, end).
    """
    dir = os.path.join(output_dir, 'acorduri')
    os.makedirs(dir, exist_ok=True)
    output_file = os.path.join(dir, 'acorduri.csv')

    if os.path.isfile(output_file):
        print(f"\tFișierul '{output_file}' există deja. Îl voi suprascrie.")
    else:
        print(f"\tFișierul '{output_file}' nu există. Îl voi crea.")

    segmente = acorduri(partitura)
    if not segmente:
        print(f"\tNu s-au găsit segmente pentru acorduri.")
        return

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['start', 'end', 'segment_name'])
            for idx, (figura, start, end) in enumerate(segmente, 1):
                figura_str = figura.replace(' ', '_') if figura else 'Unknown'
                writer.writerow([f"{start:.3f}", f"{end:.3f}", f"Acord_{idx}_{figura_str}"])
        print(f"\tRezultatele au fost salvate în fișierul: '{output_file}'")
    except Exception as e:
        print(f"\tEroare la scrierea fișierului: {e}")

    return segmente

def vizualizare_tonalitate(partitura, output_dir):
    """
    Creează un grafic pentru segmentele de tonalitate.

    Args:
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.
        output_dir (str): directorul unde sunt salvate informațiile (output_dir/output_subdir).
    """
    segmente = segmentare_tonalitate(partitura, output_dir)
    if not segmente:
        print("\tNu există segmente de tonalitate pentru vizualizare.")
        return

    total_duration = partitura.duration.quarterLength
    colors = ['skyblue', 'lightgreen', 'lightcoral']

    fig, ax = plt.subplots(figsize=(15, 3))
    for idx, (tonalitate, start, end) in enumerate(segmente):
        tonalitate_str = str(tonalitate) if tonalitate else 'Unknown'
        ax.barh(0, end - start, left=start, height=0.4, color=colors[idx % len(colors)],
                label=tonalitate_str if idx < len(colors) else "")
        ax.text((start + end) / 2, 0, tonalitate_str, ha='center', va='center', fontsize=10, color='black')

    ax.set_yticks([0])
    ax.set_yticklabels(['Tonalitate'])
    ax.set_xlabel('Timp (quarterLength)')
    ax.set_xlim(0, total_duration - 1)
    ax.set_ylim(-0.5, 0.5)
    ax.grid(True, axis='x', linestyle='--', alpha=0.5)

    dir = os.path.join(output_dir, 'vizualizare')
    os.makedirs(dir, exist_ok=True)
    output_file = os.path.join(dir, 'tonalitate.png')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"\tVizualizarea tonalității a fost salvată în: '{output_file}'")

def vizualizare_acorduri(partitura, output_dir):
    """
    Creează un grafic pentru segmentele de acorduri.

    Args:
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.
        output_dir (str): directorul unde sunt salvate informațiile (output_dir/output_subdir).
    """
    segmente = segmentare_acorduri(partitura, output_dir)
    if not segmente:
        print("\tNu există segmente de acorduri pentru vizualizare.")
        return

    total_duration = partitura.duration.quarterLength
    colors = plt.cm.Paired.colors

    fig, ax = plt.subplots(figsize=(15, 3))
    for idx, (figura, start, end) in enumerate(segmente):
        color = colors[idx % len(colors)]
        if 'major' in figura.lower():
            color = 'lightblue'
        elif 'minor' in figura.lower():
            color = 'lightcoral'
        elif 'seventh' in figura.lower():
            color = 'lightgreen'

        ax.barh(0, end - start, left=start, height=0.4, color=color)
        if end - start >= 0.5:
            ax.text((start + end) / 2, 0, figura, ha='center', va='center', fontsize=8, color='black', rotation=45)

    ax.set_yticks([0])
    ax.set_yticklabels(['Acorduri'])
    ax.set_xlabel('Timp (quarterLength)')
    ax.set_xlim(0, total_duration - 1)
    ax.set_ylim(-0.5, 0.5)
    ax.grid(True, axis='x', linestyle='--', alpha=0.7)

    dir = os.path.join(output_dir, 'vizualizare')
    os.makedirs(dir, exist_ok=True)
    output_file = os.path.join(dir, 'acorduri.png')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()
    print(f"\tVizualizarea acordurilor a fost salvată în: '{output_file}'")

def segmentare(partitura, output_dir, output_subdir="segmentare"):
    """
    Funcția principală pentru segmentarea partiturii.
    Apelează funcțiile de segmentare bazate pe tonalitate și acorduri.

    Args:
        partitura (music21.Score): Obiect music21 Score, partitura de analizat.
        output_dir (str): directorul principal unde sunt salvate informațiile.
        output_subdir (str): subdirectorul unde se salvează segmentarea.

    Return:
        output_path (str): directorul unde sunt salvate segmentele de tonalitate și acorduri.
    """
    print(f"\tRealizez segmentarea partiturii...")
    
    # Creează directorul de ieșire dacă nu există
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_subdir)
    os.makedirs(output_path, exist_ok=True)

    if not partitura.parts:
        print("\tEroare: Partitura nu conține părți!")
        return

    # Apelează funcțiile de segmentare și vizualizare
    vizualizare_tonalitate(partitura, output_path)
    vizualizare_acorduri(partitura, output_path)

    return output_path