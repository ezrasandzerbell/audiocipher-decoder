# merged_midi_to_decoder.py

import sys
import os
import itertools
import string
from music21 import converter, note, scale, pitch

def midi_to_tone_row(midi_file_path):
    """
    Converts a MIDI file to a space-separated tone row of note names.

    Args:
        midi_file_path (str): Path to the MIDI file.

    Returns:
        str: Space-separated note names representing the tone row.
    """
    # Load the MIDI file
    try:
        midi_stream = converter.parse(midi_file_path)
    except Exception as e:
        print(f"Error loading MIDI file: {e}")
        return None

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

    return tone_row

def load_word_list():
    """
    Loads English words from the 'En.txt' file located in the NLTK data directory.

    Returns:
        set: A set of valid English words.
    """
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
        else:
            print(f"Warning: Word list file '{filename}' not found in '{nltk_data_path}'.")
    return words

def load_name_list():
    """
    Loads names from the 'names.txt' file located in the NLTK data directory.

    Returns:
        set: A set of valid names.
    """
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
        else:
            print(f"Warning: Name list file '{filename}' not found in '{nltk_data_path}'.")
    return names

def is_valid_phrase(phrase, all_names, english_words):
    """
    Validates whether a phrase consists of valid English words or names.

    Args:
        phrase (list): List of words in the phrase.
        all_names (set): Set of valid names.
        english_words (set): Set of valid English words.

    Returns:
        bool: True if the phrase is valid, False otherwise.
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
    Creates a mapping from letters to note names based on the given scale.
    Ensures that 'w' maps to the same note as 'i'.

    Args:
        sc (music21.scale.Scale): The musical scale to use for mapping.

    Returns:
        dict: A dictionary mapping each lowercase letter to a note name.
    """
    letters = string.ascii_lowercase
    mapping = {}
    idx = 0
    degrees = list(range(1, 8)) if not isinstance(sc, scale.ChromaticScale) else list(range(1, 13))
    degree_count = len(degrees)
    while len(mapping) < 26:
        degree = degrees[idx % degree_count]
        try:
            p = sc.pitchFromDegree(degree)
            pitch_name = p.name
        except Exception as e:
            print(f"Error mapping degree {degree} in scale {sc}: {e}")
            return mapping
        mapping[letters[idx]] = pitch_name
        idx += 1

    # Ensure 'w' maps to the same note as 'i'
    if 'i' in mapping:
        mapping['w'] = mapping['i']
    else:
        print("Error: Letter 'i' not found in mapping. Cannot map 'w' to 'i's note.")

    return mapping

def reverse_mapping(mapping):
    """
    Reverses the letter-to-note mapping to a note-to-letters mapping.

    Args:
        mapping (dict): Dictionary mapping letters to note names.

    Returns:
        dict: Dictionary mapping note names to lists of letters.
    """
    note_to_letters = {}
    for letter, pitch_name in mapping.items():
        if pitch_name not in note_to_letters:
            note_to_letters[pitch_name] = []
        note_to_letters[pitch_name].append(letter)
    return note_to_letters

def segment_into_words(s, english_words, all_names, max_word_length):
    """
    Segments a string into all valid phrases with the fewest number of words using dynamic programming.

    Args:
        s (str): The string to segment.
        english_words (set): Set of valid English words.
        all_names (set): Set of valid names.
        max_word_length (int): Maximum length of a word.

    Returns:
        list of lists or None: List of all possible word lists if segmentation is possible, else None.
    """
    n = len(s)
    dp = [[] for _ in range(n + 1)]
    dp[0] = [[]]  # Initialize with empty list

    for i in range(1, n + 1):
        current_phrases = []
        for j in range(max(0, i - max_word_length), i):
            word = s[j:i]
            if word in english_words or word in all_names:
                for phrase in dp[j]:
                    current_phrases.append(phrase + [word])
        dp[i] = current_phrases

    if not dp[n]:
        return None

    # Find the minimal number of words
    min_num_words = min(len(phrase) for phrase in dp[n])

    # Collect all phrases that have the minimal number of words
    best_phrases = [phrase for phrase in dp[n] if len(phrase) == min_num_words]

    return best_phrases

def decode_melody(note_to_letters, melody):
    """
    Decodes a melody into possible letter combinations based on the note-to-letters mapping.

    Args:
        note_to_letters (dict): Mapping from note names to lists of possible letters.
        melody (list): List of note names representing the melody.

    Returns:
        list: List of decoded strings.
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
            except:
                letters = []
        if letters:
            possible_letters.append(letters)
        else:
            return []
    combinations = list(itertools.product(*possible_letters))
    decoded_strings = [''.join(combo) for combo in combinations]
    return decoded_strings

def main():
    """
    Main function that merges MIDI to Tone Row conversion and Tone Row decoding.
    """
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python merged_midi_to_decoder.py <midi_file_path>")
        sys.exit(1)

    midi_file_path = sys.argv[1]
    if not os.path.isfile(midi_file_path):
        print(f"File not found: {midi_file_path}")
        sys.exit(1)

    # Convert MIDI to Tone Row
    tone_row = midi_to_tone_row(midi_file_path)
    if tone_row is None:
        sys.exit(1)

    print(f"Tone Row: {tone_row}\n")

    # Load word lists
    english_words = load_word_list()
    all_names = load_name_list()
    if not english_words and not all_names:
        print("No words or names loaded. Please check your word and name files.")
        sys.exit(1)

    max_word_length = max(len(word) for word in english_words.union(all_names)) if (english_words or all_names) else 0

    # Process the tone row
    melody_notes = tone_row.strip().split()
    valid_note_names = [
        'C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'E#', 'F', 'F#', 'G-',
        'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B', 'B#', 'C-', 'F-'
    ]
    melody_notes = [n.upper() for n in melody_notes]
    for n in melody_notes:
        if n not in valid_note_names:
            print(f"Invalid note name: {n}")
            sys.exit(1)

    results = []

    # Define root notes and modes
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

    # Decode the melody for each root and mode
    for decode_root in root_notes:
        for decode_mode_name, decode_mode_class in modes.items():
            try:
                decode_sc = decode_mode_class(decode_root)
            except:
                # If the scale cannot be constructed with the given root, skip
                continue
            note_letter_map = reverse_mapping(create_letter_note_mapping(decode_sc))
            decoded_strings = decode_melody(note_letter_map, melody_notes)
            for decoded_str in decoded_strings:
                phrase_lists = segment_into_words(decoded_str, english_words, all_names, max_word_length)
                if phrase_lists:
                    for phrase in phrase_lists:
                        if is_valid_phrase(phrase, all_names, english_words):
                            results.append({
                                'phrase': ' '.join(phrase),
                                'decoded_root_note': decode_root,
                                'decoded_scale': decode_mode_name,
                                'num_words': len(phrase)
                            })

    # Remove duplicate results
    unique_results = { (r['phrase'], r['decoded_root_note'], r['decoded_scale']): r for r in results }.values()

    # Find the best phrases with the fewest number of words
    if unique_results:
        # Sort the results alphabetically by phrase
        sorted_results = sorted(unique_results, key=lambda x: x['phrase'].lower())

        # Determine the minimal number of words
        min_num_words = min(r['num_words'] for r in sorted_results)

        # Collect all phrases that have the minimal number of words
        best_phrases = [r for r in sorted_results if r['num_words'] == min_num_words]

        print("Best Phrases with the Fewest Number of Words (Alphabetically Ordered):")
        for r in best_phrases:
            print(f"Phrase: \"{r['phrase']}\", Decoded in: {r['decoded_scale']} scale starting at {r['decoded_root_note']}")
    else:
        print("No valid English phrases found for the given tone row.")

if __name__ == "__main__":
    main()
