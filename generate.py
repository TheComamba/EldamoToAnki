import argparse
import copy
import os
import requests
import xml.etree.ElementTree as ElementTree

INPUT_URL = "https://github.com/pfstrack/eldamo/raw/master/src/data/eldamo-data.xml"
INPUT_FILE = "input/eldamo-data.xml"

KHUZDUL = { "id": "kh", "name": "Khuzdul" }
NEO_QUENYA = { "id": "nq", "name": "Neo-Quenya"}
NEO_SINDARIN = { "id": "ns", "name": "Neo-Sindarin"}
QUENYA = { "id": "q", "name": "Quenya"}
SINDARIN = { "id": "s", "name": "Sindarin"}
SUPPORTED_LANGUAGES = [KHUZDUL, QUENYA, SINDARIN, NEO_QUENYA, NEO_SINDARIN]

SPEECH_INDIVIDUAL_NAMES = ["fem-name", "masc-name", "place-name"]
SPEECH_COLLECTIVE_NAMES = "collective-name"
SPEECH_PROPER_NAMES = "proper-name"
SPEECH_PHRASES = "phrase"
SPEECH_EXCLUDES = ["grammar", "phoneme", "phonetic-rule", "phonetic-group", "phonetics", "root", "text", "?"]

DELIMITER = "|"

# TODO: If neo words is active, prefer ngloss over gloss.
# TODO: Can we update the cards instead of reimporting them?
# TODO: Make language argument positional.

def parse_args():
    parser = argparse.ArgumentParser(description='Generate text files that are easily imported with Anki.')
    parser.add_argument('--language', type=str, required=True, help='Language to generate')
    parser.add_argument('--neo-words', action='store_true', default=False, help='Include words invented by fans rather than Tolkien')
    parser.add_argument('--individual-names', action='store_true', default=False, help='Include names of individuals and places')
    parser.add_argument('--collective-names', action='store_true', default=False, help='Include names for collective people')
    parser.add_argument('--proper-names', action='store_true', default=False, help='Include proper names')
    parser.add_argument('--phrases', action='store_true', default=False, help='Include phrases')
    parser.add_argument('--check-for-updates', action='store_true', default=False, help='Forces a re-download of the Eldamo database')

    return parser.parse_args()

def ensure_endamo_data(args):
    dir_name = os.path.dirname(INPUT_FILE)

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    if not os.path.exists(INPUT_FILE) or args.check_for_updates:
        print("Downloading Eldamo data from ", INPUT_URL, "...")
        response = requests.get(INPUT_URL)
        with open(INPUT_FILE, 'wb') as file:
            file.write(response.content)

def read_endamo_data():
    try:
        tree = ElementTree.parse(INPUT_FILE)
        root = tree.getroot()
        return root
    except FileNotFoundError:
        print(f"File {INPUT_FILE} not found.")
        return None
    
def get_languages_to_generate(args):
    languages = []
    is_supported = False
    for language in SUPPORTED_LANGUAGES:
        if args.language == language['id'] or args.language == language['name']:
            is_supported = True
            languages.append(language)
            break

    if not is_supported:
        raise ValueError(f"Unsupported language: {args.language}")
    
    if args.neo_words:
        if languages[0] == QUENYA:
            languages.append(NEO_QUENYA)
        elif languages[0] == SINDARIN:
            languages.append(NEO_SINDARIN)
        else:
            raise ValueError(f"Neo-words are not supported for {languages[0]['name']}")
    return languages

def get_speech_types_to_exclude(args):
    speech_types = copy.deepcopy(SPEECH_EXCLUDES)
    if not args.individual_names:
        speech_types.extend(SPEECH_INDIVIDUAL_NAMES)
    if not args.collective_names:
        speech_types.append(SPEECH_COLLECTIVE_NAMES)
    if not args.proper_names:
        speech_types.append(SPEECH_PROPER_NAMES)
    if not args.phrases:
        speech_types.append(SPEECH_PHRASES)
    return speech_types

def debug_print_word(word):
    element_string = ElementTree.tostring(word, encoding='utf-8').decode('utf-8')
    print(element_string)

def find_referenced_word(referencer, all_words):
    see_element = referencer.find('see')
    if see_element is None:
        return None
    reference = see_element.get('v')
    if reference is None:
        return None
    for word in all_words:
        if word.get('v') == reference:
            return word
    return None

def find_translation(all_words, word):
    english_word = word.get('gloss')
    if english_word is None:
        referenced_word = find_referenced_word(word, all_words)
        if referenced_word is not None:
            english_word = find_translation(all_words, referenced_word)
    return english_word

def format_word(all_words, word):
    tolkienian_word = word.get('v')
    if tolkienian_word is None:
        print("Skipping word without value: ")
        debug_print_word(word)
    english_word = find_translation(all_words, word)
    if english_word is None:
        print("Skipping word without translation: ", tolkienian_word)
    part_of_speech = word.get('speech')

    formatted_word = f"{tolkienian_word}{DELIMITER}{english_word}"
    if part_of_speech is not None:
        formatted_word += f" ({part_of_speech})"
    formatted_word += "\n"
    
    return formatted_word

def write_to_file(args, languages, words):
    language_name = languages[0].get("name")
    if args.neo_words:
        language_name = "(Neo-)" + language_name
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    filename = output_dir + "/" + language_name + ".txt"

    with open(filename, 'w') as f:
        for word in words:
            formatted_word = format_word(words, word)
            f.write(formatted_word)
    
    print("Written output to ", filename)

def main():
    args = parse_args()

    ensure_endamo_data(args)
    root = read_endamo_data()
    if root is not None:
        words = root.findall(".//word")

        languages = get_languages_to_generate(args)
        print("Generating cards for the following languages: ", [lang.get("name") for lang in languages])

        language_ids = [lang.get("id") for lang in languages]
        filtered_words = [word for word in words if word.get('l') in language_ids]

        speech_types_to_exclude = get_speech_types_to_exclude(args)
        filtered_words = [word for word in filtered_words if word.get('speech') not in speech_types_to_exclude]
        
        included_speech_values = [word.get('speech') for word in filtered_words]
        included_speech_values = list(set(included_speech_values))  # Remove duplicates
        included_speech_values.sort()
        print("Collected ", len(filtered_words) ," cards of the following speech types:\n", included_speech_values)

        write_to_file(args, languages, filtered_words)
    else:
        raise ValueError("Could not read Eldamo data")

main()
