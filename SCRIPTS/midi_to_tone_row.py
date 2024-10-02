# midi_to_tone_row.py

from music21 import converter, note, stream
import sys
import os

def midi_to_tone_row(midi_file_path):
    # Load the MIDI file
    try:
        midi_stream = converter.parse(midi_file_path)
    except Exception as e:
        print(f"Error loading MIDI file: {e}")
        return

    # Flatten all parts into a single stream
    flat_notes = midi_stream.flat.notes

    # Filter only notes (ignore chords and rests)
    melody_notes = [n for n in flat_notes if isinstance(n, note.Note)]

    # Sort notes by their offset to preserve the original sequence
    melody_notes.sort(key=lambda n: n.offset)

    # Extract note names (without octave numbers)
    note_names = [n.pitch.name for n in melody_notes]

    # Create space-separated format
    tone_row = ' '.join(note_names)

    print(tone_row)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python midi_to_tone_row.py <midi_file_path>")
    else:
        midi_file_path = sys.argv[1]
        if not os.path.isfile(midi_file_path):
            print(f"File not found: {midi_file_path}")
        else:
            midi_to_tone_row(midi_file_path)
