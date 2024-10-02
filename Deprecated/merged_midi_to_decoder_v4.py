# udiocipher_decoder.py

import itertools
import string
import sys
import os
from music21 import converter, note, scale, pitch
from multiprocessing import Pool, cpu_count
from functools import partial

def midi_to_tone_row(midi_file_path):
    # Load the MIDI file
    try:
        midi_stream = converter.parse(midi_file_path)
    except Exception as e:
        print(f"Error loading MIDI file: {e}")
        return None

    # Flatten all parts into a single stream using the updated .flatten() method
    flat_notes = midi_stream.flatten().notes

    # Filter only notes (ignore chords and rests)
    melody_notes = (n for n in flat_notes if isinstance(n, note.Note))

    # Sort notes by their offset to preserve the original sequence
    melody_notes = sorted(melody_notes, key=lambda n: n.offset)

    # Extract note names (without octave numbers)
    note_names = (n.pitch.name for n in melody_notes)

    # Create space-separated format
    tone_row = ' '.join(note_names)

    return tone_row

def load_word_list():
    word_files = ['En.txt']
    words = set()
    valid_single_letter_words = {'a', 'i'}
    nltk_data_path = os.path.join(os.path.expanduser('~'), 'nltk_data')
    for filename in word_files:
        filepath = os.path.join(nltk_data_path, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word and (len(word) > 1 or word in valid_single_letter_words):
                        words.add(word)
    return words

def load_name_list():
    name_files = ['names.txt']
    names = set()
    valid_single_letter_names = {'a', 'i'}
    nltk_data_path = os.path.join(os.path.expanduser('~'), 'nltk_data')
    for filename in name_files:
        filepath = os.path.join(nltk_data_path, filename)
        if os.path.isfile(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip().lower()
                    if name and (len(name) > 1 or name in valid_single_letter_names):
                        names.add(name)
    return names

def build_prefix_set(words):
    prefixes = set()
    for word in words:
        for i in range(1, len(word)):
            prefixes.add(word[:i])
    return prefixes

def is_valid_phrase(phrase, all_names, english_words):
    if not phrase:
        return False
    valid_single_letter_words = {'a', 'i'}
    for word in phrase:
        if len(word) == 1 and word not in valid_single_letter_words:
            return False
        if not (word in english_words or word in all_names):
            return False
    return True

def create_letter_note_mapping(sc):
    letters = string.ascii_lowercase
    mapping = {}
    idx = 0
    degrees = list(range(1, 8))  # Fixed to diatonic degrees 1-7
    degree_count = len(degrees)
    while len(mapping) < 26:
        degree = degrees[idx % degree_count]
        p = sc.pitchFromDegree(degree)
        pitch_name = p.name
        mapping[letters[idx]] = pitch_name
        idx += 1
    return mapping

def reverse_mapping(mapping):
    note_to_letters = {}
    for letter, pitch_name in mapping.items():
        if pitch_name not in note_to_letters:
            note_to_letters[pitch_name] = []
        note_to_letters[pitch_name].append(letter)
    return note_to_letters

def decode_melody(note_to_letters, melody):
    possible_letters = []
    for n in melody:
        letters = note_to_letters.get(n, [])
        if not letters:
            try:
                p = pitch.Pitch(n)
                enharmonic_pitch = p.getEnharmonic()
                enharmonic_name = enharmonic_pitch.name
                letters = note_to_letters.get(enharmonic_name, [])
            except:
                letters = []
        if letters:
            possible_letters.append(letters)
        else:
            return []
    # Use generator to yield combinations one by one
    return itertools.product(*possible_letters)

def segment_into_words(decoded_chars, words_set, prefixes_set, max_word_length):
    n = len(decoded_chars)
    dp = [None] * (n + 1)
    dp[0] = []
    for i in range(1, n + 1):
        for j in range(max(0, i - max_word_length), i):
            if dp[j] is not None:
                word = ''.join(decoded_chars[j:i])
                if word in words_set:
                    if dp[i] is None or len(dp[j]) + 1 < len(dp[i]):
                        dp[i] = dp[j] + [word]
                elif word in prefixes_set:
                    continue  # Possible prefix, continue
    return dp[n]

def process_root_mode(root_mode_tuple, melody_notes, words_set, prefixes_set, max_word_length, all_names, english_words):
    decode_root, decode_mode_name, decode_mode_class = root_mode_tuple
    decode_sc = decode_mode_class(decode_root)
    note_letter_map = reverse_mapping(create_letter_note_mapping(decode_sc))
    decoded_combinations = decode_melody(note_letter_map, melody_notes)
    results = []
    for decoded_chars in decoded_combinations:
        phrase = segment_into_words(decoded_chars, words_set, prefixes_set, max_word_length)
        if phrase and is_valid_phrase(phrase, all_names, english_words):
            results.append({
                'phrase': ' '.join(phrase),
                'decoded_root_note': decode_root,
                'decoded_scale': decode_mode_name,
                'num_words': len(phrase)
            })
    return results

def decode_tone_row_parallel(tone_row, root_modes, words_set, prefixes_set, max_word_length, all_names, english_words):
    melody_notes = tone_row.strip().split()
    valid_note_names = [
        'C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'E#', 'F', 'F#', 'G-',
        'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B', 'B#', 'C-', 'F-'
    ]
    melody_notes = [n.upper() for n in melody_notes]
    for n in melody_notes:
        if n not in valid_note_names:
            print(f"Invalid note name: {n}")
            return

    pool = Pool(processes=cpu_count())
    process_func = partial(
        process_root_mode,
        melody_notes=melody_notes,
        words_set=words_set,
        prefixes_set=prefixes_set,
        max_word_length=max_word_length,
        all_names=all_names,
        english_words=english_words
    )
    all_results = pool.map(process_func, root_modes)
    pool.close()
    pool.join()

    # Flatten the list of results
    flat_results = list(itertools.chain.from_iterable(all_results))

    # Remove duplicates
    unique_results = {}
    for r in flat_results:
        key = (r['phrase'], r['decoded_root_note'], r['decoded_scale'])
        if key not in unique_results or r['num_words'] < unique_results[key]['num_words']:
            unique_results[key] = r

    if unique_results:
        min_num_words = min(r['num_words'] for r in unique_results.values())
        best_phrases = [r for r in unique_results.values() if r['num_words'] == min_num_words]
        print("\nBest Phrases with the Fewest Number of Words:")
        for r in best_phrases:
            print(f"Phrase: \"{r['phrase']}\", Decoded in: {r['decoded_scale']} scale starting at {r['decoded_root_note']}")
    else:
        print("No valid English phrases found for the given tone row.")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 udiocipher_decoder.py <midi_file_path>")
        return
    midi_file_path = sys.argv[1]
    if not os.path.isfile(midi_file_path):
        print(f"File not found: {midi_file_path}")
        return

    tone_row = midi_to_tone_row(midi_file_path)
    if tone_row is None:
        return

    english_words = load_word_list()
    all_names = load_name_list()
    if not english_words and not all_names:
        print("No words or names loaded. Please check your word and name files.")
        return

    # Build prefix set for early pruning
    prefixes_set = build_prefix_set(english_words.union(all_names))
    
    max_word_length = max(len(word) for word in english_words.union(all_names)) if english_words.union(all_names) else 0

    # Initialize root notes and modes
    root_notes = ['C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'F', 'F#', 'G-', 'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B']
    modes = {
        'Ionian': scale.MajorScale,
        'Dorian': scale.DorianScale,
        'Phrygian': scale.PhrygianScale,
        'Lydian': scale.LydianScale,
        'Mixolydian': scale.MixolydianScale,
        'Aeolian': scale.MinorScale,
        'Locrian': scale.LocrianScale,
        'Harmonic Minor': scale.HarmonicMinorScale,
    }

    # Prepare list of (root, mode name, mode class) tuples
    root_modes = []
    for root in root_notes:
        for mode_name, mode_class in modes.items():
            root_modes.append((root, mode_name, mode_class))

    # Call the parallel decoding function
    decode_tone_row_parallel(tone_row, root_modes, english_words, prefixes_set, max_word_length, all_names, english_words)

if __name__ == "__main__":
    main()
