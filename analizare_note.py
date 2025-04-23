from music21 import *
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt

def analiza_distributie_pitch(csv_file, output_dir="analize"):
    """
    Analizează distribuția înălțimilor și salvează rezultatele + grafice.
    """
    df = pd.read_csv(csv_file)
    note_df = df[df['type'] == 'Note']
    
    # Distribuția pitch-urilor (toate vocile)
    pitch_counts = note_df['pitch'].value_counts().reset_index()
    pitch_counts.columns = ['pitch', 'count']
    output_file = os.path.join(output_dir, "pitch_distribution_all.csv")
    pitch_counts.to_csv(output_file, index=False)
    print(f"Distribuția pitch-urilor (toate vocile) salvată în: {output_file}")
    
    # Grafic toate vocile
    plt.figure(figsize=(10, 5))
    pitch_counts.set_index('pitch')['count'].plot(kind='bar')
    plt.title("Distribuția înălțimilor (toate vocile)")
    plt.xlabel("Pitch")
    plt.ylabel("Frecvență")
    plt.xticks(rotation=45)
    plt.tight_layout()
    graph_file = os.path.join(output_dir, "pitch_distribution_all.png")
    plt.savefig(graph_file)
    plt.close()
    print(f"Grafic pitch-uri (toate vocile) salvat în: {graph_file}")
    
    # Statistici generale
    stats = {
        'numar_note': len(note_df),
        'pitch_uri_unice': len(note_df['pitch'].unique()),
        'octava_minima': note_df['octave'].min() if not note_df.empty else None,
        'octava_maxima': note_df['octave'].max() if not note_df.empty else None
    }
    stats_file = os.path.join(output_dir, "pitch_stats_all.txt")
    with open(stats_file, 'w', encoding='utf-8') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    print(f"Statistici pitch-uri (toate vocile) salvate în: {stats_file}")
    
    # Distribuția pe voci
    instrumente = df[df['type'] == 'Instrument']['pitch'].unique()
    for instr in instrumente:
        start_idx = df[(df['type'] == 'Instrument') & (df['pitch'] == instr)].index
        note_instr = pd.DataFrame()
        for idx in start_idx:
            # Selectăm notele până la următorul Instrument sau sfârșitul fișierului
            next_instr = df[df['type'] == 'Instrument'].index
            next_idx = next_instr[next_instr > idx].min() if len(next_instr[next_instr > idx]) > 0 else len(df)
            note_temp = df.iloc[idx + 1:next_idx]
            note_temp = note_temp[note_temp['type'] == 'Note']
            note_instr = pd.concat([note_instr, note_temp])
        
        if not note_instr.empty:
            pitch_counts = note_instr['pitch'].value_counts().reset_index()
            pitch_counts.columns = ['pitch', 'count']
            output_file = os.path.join(output_dir, f"pitch_distribution_{instr}.csv")
            pitch_counts.to_csv(output_file, index=False)
            print(f"Distribuția pitch-urilor ({instr}) salvată în: {output_file}")
            
            # Grafic per voce
            plt.figure(figsize=(10, 5))
            pitch_counts.set_index('pitch')['count'].plot(kind='bar')
            plt.title(f"Distribuția înălțimilor ({instr})")
            plt.xlabel("Pitch")
            plt.ylabel("Frecvență")
            plt.xticks(rotation=45)
            plt.tight_layout()
            graph_file = os.path.join(output_dir, f"pitch_distribution_{instr}.png")
            plt.savefig(graph_file)
            plt.close()
            print(f"Grafic pitch-uri ({instr}) salvat în: {graph_file}")
            
            stats = {
                'numar_note': len(note_instr),
                'pitch_uri_unice': len(note_instr['pitch'].unique()),
                'octava_minima': note_instr['octave'].min() if not note_instr.empty else None,
                'octava_maxima': note_instr['octave'].max() if not note_instr.empty else None
            }
            stats_file = os.path.join(output_dir, f"pitch_stats_{instr}.txt")
            with open(stats_file, 'w', encoding='utf-8') as f:
                for key, value in stats.items():
                    f.write(f"{key}: {value}\n")
            print(f"Statistici pitch-uri ({instr}) salvate în: {stats_file}")

def analiza_ritm(csv_file, output_dir="analize"):
    """
    Analizează distribuția duratelor și salvează rezultatele + grafice.
    """
    df = pd.read_csv(csv_file)
    note_df = df[df['type'] == 'Note']
    
    # Distribuția duratelor
    duration_counts = note_df['duration'].value_counts().reset_index()
    duration_counts.columns = ['duration', 'count']
    output_file = os.path.join(output_dir, "duration_distribution_all.csv")
    duration_counts.to_csv(output_file, index=False)
    print(f"Distribuția duratelor (toate vocile) salvată în: {output_file}")
    
    # Grafic toate vocile
    plt.figure(figsize=(8, 5))
    duration_counts.set_index('duration')['count'].plot(kind='bar')
    plt.title("Distribuția duratelor (toate vocile)")
    plt.xlabel("Durată (quarterLength)")
    plt.ylabel("Frecvență")
    plt.tight_layout()
    graph_file = os.path.join(output_dir, "duration_distribution_all.png")
    plt.savefig(graph_file)
    plt.close()
    print(f"Grafic durate (toate vocile) salvat în: {graph_file}")
    
    # Statistici ritmice
    stats = {
        'durata_medie': note_df['duration'].mean() if not note_df.empty else None,
        'durata_minima': note_df['duration'].min() if not note_df.empty else None,
        'durata_maxima': note_df['duration'].max() if not note_df.empty else None
    }
    stats_file = os.path.join(output_dir, "rhythm_stats_all.txt")
    with open(stats_file, 'w', encoding='utf-8') as f:
        for key, value in stats.items():
            f.write(f"{key}: {value}\n")
    print(f"Statistici ritmice (toate vocile) salvate în: {stats_file}")
    
    # Pe voci
    instrumente = df[df['type'] == 'Instrument']['pitch'].unique()
    for instr in instrumente:
        start_idx = df[(df['type'] == 'Instrument') & (df['pitch'] == instr)].index
        note_instr = pd.DataFrame()
        for idx in start_idx:
            next_instr = df[df['type'] == 'Instrument'].index
            next_idx = next_instr[next_instr > idx].min() if len(next_instr[next_instr > idx]) > 0 else len(df)
            note_temp = df.iloc[idx + 1:next_idx]
            note_temp = note_temp[note_temp['type'] == 'Note']
            note_instr = pd.concat([note_instr, note_temp])
        
        if not note_instr.empty:
            duration_counts = note_instr['duration'].value_counts().reset_index()
            duration_counts.columns = ['duration', 'count']
            output_file = os.path.join(output_dir, f"duration_distribution_{instr}.csv")
            duration_counts.to_csv(output_file, index=False)
            print(f"Distribuția duratelor ({instr}) salvată în: {output_file}")
            
            # Grafic per voce
            plt.figure(figsize=(8, 5))
            duration_counts.set_index('duration')['count'].plot(kind='bar')
            plt.title(f"Distribuția duratelor ({instr})")
            plt.xlabel("Durată (quarterLength)")
            plt.ylabel("Frecvență")
            plt.tight_layout()
            graph_file = os.path.join(output_dir, f"duration_distribution_{instr}.png")
            plt.savefig(graph_file)
            plt.close()
            print(f"Grafic durate ({instr}) salvat în: {graph_file}")
            
            stats = {
                'durata_medie': note_instr['duration'].mean() if not note_instr.empty else None,
                'durata_minima': note_instr['duration'].min() if not note_instr.empty else None,
                'durata_maxima': note_instr['duration'].max() if not note_instr.empty else None
            }
            stats_file = os.path.join(output_dir, f"rhythm_stats_{instr}.txt")
            with open(stats_file, 'w', encoding='utf-8') as f:
                for key, value in stats.items():
                    f.write(f"{key}: {value}\n")
            print(f"Statistici ritmice ({instr}) salvate în: {stats_file}")

def analiza_densitate(csv_file, output_dir="analize", bin_size=1.0):
    """
    Analizează densitatea notelor în timp și salvează rezultatele + grafice.
    """
    df = pd.read_csv(csv_file)
    note_df = df[df['type'] == 'Note']
    
    # Grupare pe intervale de timp
    note_df = note_df.copy()
    note_df['time_bin'] = (note_df['offset'] // bin_size) * bin_size
    density = note_df.groupby('time_bin').size().reset_index()
    density.columns = ['time_bin', 'count']
    output_file = os.path.join(output_dir, "density_all.csv")
    density.to_csv(output_file, index=False)
    print(f"Densitatea notelor (toate vocile) salvată în: {output_file}")
    
    # Grafic toate vocile
    plt.figure(figsize=(10, 5))
    plt.plot(density['time_bin'], density['count'], marker='o')
    plt.title("Densitatea notelor în timp (toate vocile)")
    plt.xlabel("Timp (quarterLength)")
    plt.ylabel("Număr note")
    plt.grid(True)
    plt.tight_layout()
    graph_file = os.path.join(output_dir, "density_all.png")
    plt.savefig(graph_file)
    plt.close()
    print(f"Grafic densitate (toate vocile) salvat în: {graph_file}")
    
    # Pe voci
    instrumente = df[df['type'] == 'Instrument']['pitch'].unique()
    for instr in instrumente:
        start_idx = df[(df['type'] == 'Instrument') & (df['pitch'] == instr)].index
        note_instr = pd.DataFrame()
        for idx in start_idx:
            next_instr = df[df['type'] == 'Instrument'].index
            next_idx = next_instr[next_instr > idx].min() if len(next_instr[next_instr > idx]) > 0 else len(df)
            note_temp = df.iloc[idx + 1:next_idx]
            note_temp = note_temp[note_temp['type'] == 'Note']
            note_instr = pd.concat([note_instr, note_temp])
        
        if not note_instr.empty:
            note_instr['time_bin'] = (note_instr['offset'] // bin_size) * bin_size
            density = note_instr.groupby('time_bin').size().reset_index()
            density.columns = ['time_bin', 'count']
            output_file = os.path.join(output_dir, f"density_{instr}.csv")
            density.to_csv(output_file, index=False)
            print(f"Densitatea notelor ({instr}) salvată în: {output_file}")
            
            # Grafic per voce
            plt.figure(figsize=(10, 5))
            plt.plot(density['time_bin'], density['count'], marker='o')
            plt.title(f"Densitatea notelor în timp ({instr})")
            plt.xlabel("Timp (quarterLength)")
            plt.ylabel("Număr note")
            plt.grid(True)
            plt.tight_layout()
            graph_file = os.path.join(output_dir, f"density_{instr}.png")
            plt.savefig(graph_file)
            plt.close()
            print(f"Grafic densitate ({instr}) salvat în: {graph_file}")