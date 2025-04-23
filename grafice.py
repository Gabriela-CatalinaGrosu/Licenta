import os
import pandas as pd
import matplotlib.pyplot as plt

def grafic_distributie(instr, pitch_counts, output_dir = 'grafice_analizare'):
    # Grafic toate vocile
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
    print(f"Grafic pitch-uri {instr} salvat în: {graph_file}")

def grafic_distributie_ritm(instr, duration_counts, output_dir = 'grafice_analizare'):
    # Grafic toate vocile
    plt.figure(figsize=(10, 5))
    duration_counts.set_index('duration')['count'].plot(kind='bar')
    plt.title(f"Distribuția duratelor ({instr})")
    plt.xlabel("Durată (quarterLength)")
    plt.ylabel("Frecvență")
    plt.xticks(rotation=45)
    plt.tight_layout()
    graph_file = os.path.join(output_dir, f"duration_distribution_{instr}.png")
    plt.savefig(graph_file)
    plt.close()
    print(f"Grafic durate {instr} salvat în: {graph_file}")

def grafic_densitate(instr, density, output_dir = 'grafice_analizare'):
    # Grafic toate vocile
    plt.figure(figsize=(10, 5))
    density.set_index('time_bin')['count'].plot(kind='bar')
    plt.title(f"Densitatea notelor în timp ({instr})")
    plt.xlabel("Timp (quarterLength)")
    plt.ylabel("Număr note")
    plt.xticks(rotation=45)
    plt.tight_layout()
    graph_file = os.path.join(output_dir, f"density_{instr}.png")
    plt.savefig(graph_file)
    plt.close()
    print(f"Grafic densitate {instr} salvat în: {graph_file}")
