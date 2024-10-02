import itertools
import string
from music21 import scale, pitch
import os

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
    degrees = list(range(1, 8)) if not isinstance(sc, scale.ChromaticScale) else list(range(1, 13))
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

def segment_into_words(s, english_words, all_names, max_word_length):
    n = len(s)
    dp = [None] * (n + 1)
    dp[0] = []
    for i in range(1, n + 1):
        for j in range(max(0, i - max_word_length), i):
            word = s[j:i]
            if word in english_words or word in all_names:
                if dp[j] is not None:
                    if dp[i] is None or len(dp[j]) + 1 < len(dp[i]):
                        dp[i] = dp[j] + [word]
    return dp[n]

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
    combinations = list(itertools.product(*possible_letters))
    decoded_strings = [''.join(combo) for combo in combinations]
    return decoded_strings

def main():
    english_words = load_word_list()
    all_names = load_name_list()
    if not english_words and not all_names:
        print("No words or names loaded. Please check your word and name files.")
        return
    max_word_length = max(len(word) for word in english_words.union(all_names))
    
    # Include all root notes
    root_notes = ['C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'F', 'F#', 'G-', 'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B']
    # Include all modes
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
    print("Enter a tone row to decipher.")
    print("Format: Enter note names separated by spaces (e.g., C# A F#)")
    print("Use standard note names (A, Bb, C#, etc.)")
    input_tone_row = input("Tone row: ").strip()
    if not input_tone_row:
        print("No input provided.")
        return
    melody_notes = input_tone_row.strip().split()
    valid_note_names = [
        'C', 'C#', 'D-', 'D', 'D#', 'E-', 'E', 'E#', 'F', 'F#', 'G-',
        'G', 'G#', 'A-', 'A', 'A#', 'B-', 'B', 'B#', 'C-', 'F-'
    ]
    melody_notes = [n.upper() for n in melody_notes]
    for n in melody_notes:
        if n not in valid_note_names:
            print(f"Invalid note name: {n}")
            return
    results = []
    for decode_root in root_notes:
        for decode_mode_name, decode_mode_class in modes.items():
            decode_sc = decode_mode_class(decode_root)
            note_letter_map = reverse_mapping(create_letter_note_mapping(decode_sc))
            decoded_strings = decode_melody(note_letter_map, melody_notes)
            for decoded_str in decoded_strings:
                phrase = segment_into_words(decoded_str, english_words, all_names, max_word_length)
                if phrase and is_valid_phrase(phrase, all_names, english_words):
                    results.append({
                        'phrase': ' '.join(phrase),
                        'decoded_root_note': decode_root,
                        'decoded_scale': decode_mode_name,
                        'num_words': len(phrase)
                    })
    unique_results = { (r['phrase'], r['decoded_root_note'], r['decoded_scale']): r for r in results }.values()
    if unique_results:
        min_num_words = min(r['num_words'] for r in unique_results)
        best_phrases = [r for r in unique_results if r['num_words'] == min_num_words]
        print("\nBest Phrases with the Fewest Number of Words:")
        for r in best_phrases:
            print(f"Phrase: \"{r['phrase']}\", Decoded in: {r['decoded_scale']} scale starting at {r['decoded_root_note']}")
    else:
        print("No valid English phrases found for the given tone row.")

if __name__ == "__main__":
    main()
