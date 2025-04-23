from basic_pitch.inference import predict
from basic_pitch import ICASSP_2022_MODEL_PATH

def convert_audio_to_midi(audio_file, midi_output="temp.mid"):
    print(f"\tConverting {audio_file} to MIDI...")
    midi_data, _, _ = predict(audio_file, model_path=ICASSP_2022_MODEL_PATH)
    midi_data.write(midi_output)
    return midi_output
