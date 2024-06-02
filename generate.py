import argparse
import copy
import os
import requests
import xml.etree.ElementTree as ElementTree

INPUT_URL = "https://github.com/pfstrack/eldamo/raw/master/src/data/eldamo-data.xml"
INPUT_FILE = "input/eldamo-data.xml"

ADUNAIC = { "id": "ad", "name": "Adunaic" }
BLACK_SPEECH = { "id": "bs", "name": "Black-Speech" }
KHUZDUL = { "id": "kh", "name": "Khuzdul" }
NOLDORIN = { "id": "n", "name": "Noldorin" }
QUENYA = { "id": "q", "name": "Quenya"}
NEO_QUENYA = { "id": "nq", "name": "Neo-Quenya"}
SINDARIN = { "id": "s", "name": "Sindarin"}
NEO_SINDARIN = { "id": "ns", "name": "Neo-Sindarin"}
TELERIN = { "id": "t", "name": "Telerin"}
SUPPORTED_LANGUAGES = [ADUNAIC, BLACK_SPEECH, KHUZDUL, NOLDORIN, QUENYA, SINDARIN, TELERIN]

SPEECH_INDIVIDUAL_NAMES = ["fem-name", "masc-name", "place-name"]
SPEECH_COLLECTIVE_NAMES = "collective-name"
SPEECH_PROPER_NAMES = "proper-name"
SPEECH_PHRASES = "phrase"
SPEECH_EXCLUDES = ["grammar", "phoneme", "phonetic-rule", "phonetic-group", "phonetics", "root", "text", "?"]

DELIMITER = "|"

def parse_args():
    parser = argparse.ArgumentParser(description='Generate text files that are easily imported with Anki.')
    parser.add_argument('language', type=str, help='Language to generate')
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
        if args.language.lower() == language['id'].lower() or args.language.lower() == language['name'].lower():
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

def find_translation(all_words, word, args):
    english_word = None
    if args.neo_words:
        english_word = word.get('ngloss')
    if english_word is None:
        english_word = word.get('gloss')
    if english_word is None:
        referenced_word = find_referenced_word(word, all_words)
        if referenced_word is not None:
            english_word = find_translation(all_words, referenced_word, args)
    return english_word

def get_category(word, categories):
    category_id = word.get('cat')
    if category_id is not None:
        for cat in categories:
            if category_id.startswith(cat.get("id")):
                return cat.get("label")
    return None

def word_to_map(all_words, word, categories, args):
    word_map = {}
    word_map["tolkienian_word"] = word.get('v')
    if word_map.get("tolkienian_word") is None:
        print("Skipping word without value: ")
        debug_print_word(word)
        return None
    word_map["english_word"] = find_translation(all_words, word, args)
    if word_map.get("english_word") is None:
        print("Skipping word without translation: ", word_map.get("tolkienian_word"))
        return None
    word_map["part_of_speech"] = word.get('speech')
    word_map["stem"] = word.get('stem')
    word_map["category"] = get_category(word, categories)

    for key in word_map.keys():
        if word_map.get(key) is not None:
            word_map[key] = word_map[key].replace(DELIMITER, "")

    return word_map

def words_to_maps(all_words, words, categories, args):
    word_maps = []
    for word in words:
        word_map = word_to_map(all_words, word, categories, args)
        if word_map is not None:
            word_maps.append(word_map)
    return word_maps

def remove_duplication_marker(word):
    word["tolkienian_word"] = word["tolkienian_word"].replace("¹", "")
    word["tolkienian_word"] = word["tolkienian_word"].replace("²", "")
    word["tolkienian_word"] = word["tolkienian_word"].replace("³", "")
    word["tolkienian_word"] = word["tolkienian_word"].replace("⁴", "")
    word["tolkienian_word"] = word["tolkienian_word"].replace("⁵", "")
    word["tolkienian_word"] = word["tolkienian_word"].replace("⁶", "")
    word["tolkienian_word"] = word["tolkienian_word"].replace("⁷", "")
    word["tolkienian_word"] = word["tolkienian_word"].replace("⁸", "")
    word["tolkienian_word"] = word["tolkienian_word"].replace("⁹", "")
    word["tolkienian_word"] = word["tolkienian_word"].replace("⁰", "")

def find_tolkienian_duplicates(all_words, word_input):
    duplicates = []
    for word_iter in all_words:
        if are_tolkienian_duplicates(word_input, word_iter):
            duplicates.append(word_iter)
    return duplicates

def are_tolkienian_duplicates(word1, word2):
    if word1.get("tolkienian_word") is None or word2.get("tolkienian_word") is None:
        return False
    if word1.get("tolkienian_word") != word2.get("tolkienian_word"):
        return False
    if word1.get("stem") != word2.get("stem"):
        return False
    if word1.get("extra_info") != word2.get("extra_info"):
        return False
    return True

def find_english_duplicates(all_words, word_input):
    duplicates = []
    for word_iter in all_words:
        if are_english_duplicates(word_input, word_iter):
            duplicates.append(word_iter)
    return duplicates
    
def are_english_duplicates(word1, word2):
    if word1.get("english_word") is None or word2.get("english_word") is None:
        return False
    if word1.get("english_word") != word2.get("english_word"):
        return False
    if word1.get("part_of_speech") != word2.get("part_of_speech"):
        return False
    return True

def is_field_same_for_all(duplicates, field):
    for word in duplicates:
        if word.get(field) != duplicates[0].get(field):
            return False
    return True

def add_uniqueness_via_field(duplicates, field):
    for word in duplicates:
        if not is_field_same_for_all(duplicates, field) and word.get(field) is not None:
            if word.get("extra_info") is None:
                word["extra_info"] = ""
            else:
                word["extra_info"] += ", "
            word["extra_info"] += word.get(field)

def invalidate_word(word):
    word["tolkienian_word"] = None
    word["english_word"] = None

def merge_tolkienian_duplicates(duplicates):
    # TODO: This is currently buggy.
    english_meanings = [word.get("english_word") for word in duplicates if word.get("english_word") is not None]
    english_meanings.sort()
    counter = 1
    translation = ""
    for meaning in english_meanings:
        translation += f"({counter}) {meaning}; "
        counter += 1
    for i in range(1, len(duplicates)):
        if i == 1:
            duplicates[i]["english_word"] = translation
        else:
            invalidate_word(duplicates[i])

def make_tolkienian_duplicates_unique(duplicates):
    add_uniqueness_via_field(duplicates, "part_of_speech")
    duplicates = find_tolkienian_duplicates(duplicates, duplicates[0])
    add_uniqueness_via_field(duplicates, "category")
    duplicates = find_tolkienian_duplicates(duplicates, duplicates[0])

    if len(duplicates) > 1:
        merge_tolkienian_duplicates(duplicates)

def remove_duplications(all_words):
    for word in all_words:
        remove_duplication_marker(word)
    for word in all_words:
        if word.get("tolkienian_word") is None:
            continue
        tolkienian_duplicates = find_tolkienian_duplicates(all_words, word)
        if len(tolkienian_duplicates) > 1:
            make_tolkienian_duplicates_unique(tolkienian_duplicates)
        english_duplicates = find_english_duplicates(all_words, word)
        #if len(english_duplicates) > 1:
            # print("Found ", len(english_duplicates), " duplicates for ", english_duplicates[0].get("english_word"))
            # TODO: implement more
    all_words = [word for word in all_words if word.get("tolkienian_word") is not None]
    return all_words

def format_word(word):
    tolkienian = word.get("tolkienian_word")
    stem = word.get("stem")
    extra_info = word.get("extra_info")
    english = word.get("english_word")
    part_of_speech = word.get("part_of_speech")

    formatted_word = f"{tolkienian}"
    if stem is not None:
        formatted_word += f" ({stem})"
    if extra_info is not None:
        formatted_word += f" ({extra_info})"
    formatted_word += f"{DELIMITER}"
    formatted_word += f"{english}"
    if part_of_speech is not None:
        formatted_word += f" ({part_of_speech})"
    formatted_word += "\n"
    
    return formatted_word

def format_words(words):
    formatted_words = []
    for word in words:
        formatted_word = format_word(word)
        if formatted_word is not None:
            formatted_words.append(formatted_word)
    formatted_words.sort()
    return formatted_words

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
            f.write(word)
    
    print("Written output to ", filename)

def print_parts_of_speech(filtered_words):
    included_speech_values = [word.get('speech') for word in filtered_words]
    included_speech_values = list(set(included_speech_values))  # Remove duplicates
    included_speech_values.sort()
    print("Collected ", len(filtered_words) ," cards of the following speech types:\n", included_speech_values)

def main(args):
    languages = get_languages_to_generate(args)
    print("Generating cards for the following languages: ", [lang.get("name") for lang in languages])
    language_ids = [lang.get("id") for lang in languages]
    speech_types_to_exclude = get_speech_types_to_exclude(args)

    ensure_endamo_data(args)
    root = read_endamo_data()
    if root is not None:
        categoriy_entries = root.findall(".//cat-group")
        categories = [{ "id": cat.get("id"), "label": cat.get("label") }  for cat in categoriy_entries]

        words = root.findall(".//word")
        
        filtered_words = [word for word in words if word.get('l') in language_ids]
        filtered_words = [word for word in filtered_words if word.get('speech') not in speech_types_to_exclude]
        
        print_parts_of_speech(filtered_words)

        word_maps = words_to_maps(filtered_words, filtered_words, categories, args)

        word_maps = remove_duplications(word_maps)

        formatted_words = format_words(word_maps)

        write_to_file(args, languages, formatted_words)
    else:
        raise ValueError("Could not read Eldamo data")

if __name__ == "__main__":
    args = parse_args()
    main(args)
