# audiocipher-decoder

# AudioCipher Decoder

**AudioCipher Decoder** is an open-source project developed by **AudioCipher Technologies** that bridges the world of language and music. 

The AudioCipher DAW plugin **encodes** words and phrases into melodies and chord progressions.

This Python script can **decode** MIDI files created from AudioCipher's melody mode and return a list of possibilities in readable text.

## How It Works

### Encoding with AudioCipher MIDI Vault

To encode your words into melodies, simply use the [AudioCipher MIDI Vault plugin](https://www.audiocipher.com). Here's a quick guide to get you started:

1. **Switch to Melody Mode:**  
   Open the MIDI Vault plugin and navigate to the Text-to-MIDI generator's Melody Mode.

2. **Choose Your Scale:**  
   Select a root note and musical scale that suits your desired sound.

3. **Type in Your Message:**  
   Enter a word or phrase of up to **9 letters**.

4. **Generate the MIDI File:**  
   Click the **"Drag to MIDI"** button and save the generated MIDI file to a folder on your hard drive.

### Decoding with AudioCipher Decoder

To decode melodies back into text, use the provided Python script in this repository. The decoding process analyzes the MIDI file to retrieve the original message.

## Getting Started

### 1. Clone the Repository:

bash
git clone https://github.com/AudioCipher/audiocipher-decoder.git
cd audiocipher-decoder


### 2. Install the required Python libraries using `pip`:

To install the necessary dependencies, use the following command:

`pip install music21`

## Running the Decoder Script

Follow these steps to decode your MIDI file back into text.

### 1. Prepare Your MIDI File:

Ensure you have a MIDI file generated using the AudioCipher MIDI Vault plugin as described in the encoding section.

### 2. Place Your MIDI File in the Repository Directory:

Move or copy your MIDI file into the `audiocipher-decoder` directory (the root directory of this repository).

### 3. Open the Terminal:

- **Windows:** Press `Win + R`, type `cmd`, and press Enter.
- **macOS/Linux:** Open your preferred terminal application.

### 4. Navigate to the Repository Directory:

If you're not already in the `audiocipher-decoder` directory, navigate to it using the `cd` command:

`cd path/to/audiocipher-decoder`

*Replace `path/to/audiocipher-decoder` with the actual path to the cloned repository.*

### 5. Run the Decoder Script:

Execute the Python script. The script will automatically process all MIDI files in the `/MIDI` directory:

`python3 udiocipher_decoder.py`

### 6. Processing Time:

The algorithm will take up to **one minute** to process a 9-letter phrase but may be faster if there are fewer corresponding words.

### 7. View the Output:

The script will display all valid decoded phrases, sorted alphabetically, along with the scale and root note used for decoding.

**Example Output:**

    Extracted Tone Row: C A B B A G E
    Loaded 50000 English words.
    Loaded 1000 names.
    Built prefix set with 15000 prefixes.
    Starting decoding with 144 root-mode combinations.
    Total valid decoded phrases found: 25

    All Valid Decoded Phrases (Sorted Alphabetically):
    Phrase: "cabbage", Decoded in: C Lydian
    Phrase: "copious", Decoded in: C Lydian
    Phrase: "jawbone", Decoded in: C Lydian
    ...

---

## Contributing

As an open-source project, we invite developers, musicians, and enthusiasts to contribute, improve, and expand the capabilities of AudioCipher Decoder. Whether it's reporting bugs, suggesting features, or submitting pull requests, your contributions are highly valued. Join our community and help shape the future of musical encryption!

## License

This project is licensed under the [MIT License](LICENSE).
