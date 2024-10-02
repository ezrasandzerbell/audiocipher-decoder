# udiocipher_decoder.py

import itertools
import string
import sys
import os
import logging
from music21 import converter, note, scale, pitch
from multiprocessing import Pool, cpu_count
from functools import partial

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def midi_to_tone_row(midi_file_path):
    """
    Convert MIDI file to a space-separated string of note names.
    """
    try:
        midi_stream = converter.parse(midi_file_path)
    except Exception as e:
        logging.error(f"Error loading MIDI file: {e}")
        return None

    flat_notes = midi_stream.flatten().notes

    # Filter only single notes (ignore chords and rests)
    melody_notes = [n for n in flat_notes if isinstance(n, note.Note)]

    # Sort notes by their offset to preserve the original sequence
    melody_notes.sort(key=lambda n: n.offset)

    # Extract note names (without octave numbers)
    note_names = [n.pitch.nameWithOctave[:-1] if n.pitch.nameWithOctave.endswith(str(n.pitch.octave)) else n.pitch.name for n in melody_notes]

    # Create space-separated format
    tone_row = ' '.join(note_names)

    logging.info(f"Extracted Tone Row: {tone_row}")
    return tone_row

def load_word_list(word_file='En.txt'):
    """
    Load English words from a specified file.
    """
    words = set()
    valid_single_letter_words = {'a', 'i'}
    nltk_data_path = os.path.join(os.path.expanduser('~'), 'nltk_data')

    filepath = os.path.join(nltk_data_path, word_file)
    if not os.path.isfile(filepath):
        return words

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip().lower()
            if word and (len(word) > 1 or word in valid_single_letter_words):
                words.add(word)

    logging.info(f"Loaded {len(words)} English words.")
    return words

def load_name_list(name_file='names.txt'):
    """
    Load names from a specified file.
    """
    names = set()
    valid_single_letter_names = {'a', 'i'}
    nltk_data_path = os.path.join(os.path.expanduser('~'), 'nltk_data')

    filepath = os.path.join(nltk_data_path, name_file)
    if not os.path.isfile(filepath):
        return names

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            name = line.strip().lower()
            if name and (len(name) > 1 or name in valid_single_letter_names):
                names.add(name)

    logging.info(f"Loaded {len(names)} names.")
    return names

def build_prefix_set(words):
    """
    Build a set of all possible prefixes from the given word list.
    """
    prefixes = set()
    for word in words:
        for i in range(1, len(word)):
            prefixes.add(word[:i])
    logging.info(f"Built prefix set with {len(prefixes)} prefixes.")
    return prefixes

def is_valid_phrase(phrase, all_names, english_words):
    """
    Check if the phrase consists of valid words or names.
    """
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
    """
    Create a mapping from letters to note names based on the scale.
    """
    letters = string.ascii_lowercase
    mapping = {}
    degrees = list(range(1, 8))  # Diatonic degrees 1-7
    degree_count = len(degrees)
    idx = 0

    while len(mapping) < 26:
        degree = degrees[idx % degree_count]
        try:
            p = sc.pitchFromDegree(degree)
        except:
            logging.error(f"Invalid degree {degree} for scale {sc}")
            return {}
        pitch_name = p.name
        mapping[letters[idx]] = pitch_name
        idx += 1

    logging.debug(f"Letter to Note Mapping: {mapping}")
    return mapping

def reverse_mapping(mapping):
    """
    Reverse the letter-to-note mapping to note-to-letters.
    """
    note_to_letters = {}
    for letter, pitch_name in mapping.items():
        if pitch_name not in note_to_letters:
            note_to_letters[pitch_name] = []
        note_to_letters[pitch_name].append(letter)
    logging.debug(f"Note to Letters Mapping: {note_to_letters}")
    return note_to_letters

def decode_melody(note_to_letters, melody):
    """
    Decode the melody notes to possible letter sequences.
    """
    possible_letters = []
    for n in melody:
        letters = note_to_letters.get(n, [])
        if not letters:
            try:
                p = pitch.Pitch(n)
                enharmonic_pitch = p.getEnharmonic()
                enharmonic_name = enharmonic_pitch.name
                letters = note_to_letters.get(enharmonic_name, [])
                logging.debug(f"Using enharmonic for {n}: {enharmonic_name} -> {letters}")
            except:
                letters = []
        if letters:
            possible_letters.append(letters)
        else:
            return []
    # Generate all possible combinations
    return itertools.product(*possible_letters)

def segment_into_words(decoded_chars, words_set, prefixes_set, max_word_length):
    """
    Segment the decoded characters into valid words.
    """
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
                    continue  # Possible prefix, continue searching
    return dp[n]

def process_root_mode(root_mode_tuple, melody_notes, words_set, prefixes_set, max_word_length, all_names, english_words):
    """
    Process a single root and mode to decode the melody.
    """
    decode_root, decode_mode_name, decode_mode_class = root_mode_tuple
    try:
        decode_sc = decode_mode_class(decode_root)
        mapping = create_letter_note_mapping(decode_sc)
        if not mapping:
            return []
        note_letter_map = reverse_mapping(mapping)
        decoded_combinations = decode_melody(note_letter_map, melody_notes)
        if not decoded_combinations:
            return []

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
    except Exception as e:
        logging.error(f"Error processing {decode_root} {decode_mode_name}: {e}")
        return []

def decode_tone_row_parallel(tone_row, root_modes, words_set, prefixes_set, max_word_length, all_names, english_words):
    """
    Decode the tone row using all root and mode combinations in parallel.
    """
    melody_notes = tone_row.strip().split()
    melody_notes = [n.upper() for n in melody_notes]
    valid_note_names = set([
        'C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'E#', 'F', 'F#', 'G-',
        'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B', 'B#', 'C-', 'F-'
    ])

    for n in melody_notes:
        if n not in valid_note_names:
            logging.error(f"Invalid note name: {n}")
            return

    logging.info(f"Starting decoding with {len(root_modes)} root-mode combinations.")
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
    try:
        all_results = pool.map(process_func, root_modes)
    finally:
        pool.close()
        pool.join()

    # Flatten the list of results
    flat_results = list(itertools.chain.from_iterable(all_results))
    logging.info(f"Total valid decoded phrases found: {len(flat_results)}")

    # Remove duplicates and keep the ones with the fewest words
    unique_results = {}
    for r in flat_results:
        key = (r['phrase'], r['decoded_root_note'], r['decoded_scale'])
        if key not in unique_results or r['num_words'] < unique_results[key]['num_words']:
            unique_results[key] = r

    if unique_results:
        min_num_words = min(r['num_words'] for r in unique_results.values())
        best_phrases = [r for r in unique_results.values() if r['num_words'] == min_num_words]
        logging.info("\nBest Phrases with the Fewest Number of Words:")
        for r in best_phrases:
            print(f"Phrase: \"{r['phrase']}\", Decoded in: {r['decoded_root_note']} {r['decoded_scale']}")
    else:
        logging.info("No valid English phrases found for the given tone row.")

def main():
    if len(sys.argv) != 2:
        logging.error("Usage: python3 udiocipher_decoder.py <midi_file_path>")
        return
    midi_file_path = sys.argv[1]
    if not os.path.isfile(midi_file_path):
        logging.error(f"File not found: {midi_file_path}")
        return

    tone_row = midi_to_tone_row(midi_file_path)
    if tone_row is None:
        return

    english_words = load_word_list()
    all_names = load_name_list()
    if not english_words and not all_names:
        logging.error("No words or names loaded. Please check your word and name files.")
        return

    # Build prefix set for early pruning
    prefixes_set = build_prefix_set(english_words.union(all_names))
    
    max_word_length = max((len(word) for word in english_words.union(all_names)), default=0)

    # Initialize root notes and modes
    root_notes = [
        'C', 'C#', 'D-', 'D', 'D#', 'E-', 'E',
        'F', 'F#', 'G-', 'G', 'G#', 'A-', 'A',
        'A#', 'B-', 'B'
    ]
    modes = {
        'Major': scale.MajorScale,
        'Dorian': scale.DorianScale,
        'Phrygian': scale.PhrygianScale,
        'Lydian': scale.LydianScale,
        'Mixolydian': scale.MixolydianScale,
        'Minor': scale.MinorScale,
        'Locrian': scale.LocrianScale,
        'Harmonic Minor': scale.HarmonicMinorScale,
    }

    # Prepare list of (root, mode name, mode class) tuples
    root_modes = []
    for root in root_notes:
        for mode_name, mode_class in modes.items():
            root_modes.append((root, mode_name, mode_class))

    # Call the parallel decoding function
    decode_tone_row_parallel(
        tone_row=tone_row,
        root_modes=root_modes,
        words_set=english_words,
        prefixes_set=prefixes_set,
        max_word_length=max_word_length,
        all_names=all_names,
        english_words=english_words
    )

if __name__ == "__main__":
    main()
