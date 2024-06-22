import argparse
import copy
import os
import re
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
UNGLOSSED = "[unglossed]"

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
    if english_word == UNGLOSSED:
        english_word = None
    if english_word is None:
        english_word = word.get('gloss')
    if english_word == UNGLOSSED:
        english_word = None
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

def is_quenya(word):
    return word.get('language') == QUENYA.get('id') or word.get('language') == NEO_QUENYA.get('id')

def include_tengwar_info_for_quenya(word):
    if "þ" in word["tolkienian_word"]:
        word["tolkienian_word"] = word["tolkienian_word"].replace("þ", "s")
        word["tengwar"] = "þ"
    if word["tolkienian_word"].startswith("ñ"):
        word["tolkienian_word"] = "n" + word["tolkienian_word"][1:]
        word["tengwar"] = "ñ-"
    if word["tolkienian_word"].startswith("Ñ"):
        word["tolkienian_word"] = "N" + word["tolkienian_word"][1:]
        word["tengwar"] = "ñ-"
    if word["tolkienian_word"].startswith("w"):
        word["tolkienian_word"] = "v" + word["tolkienian_word"][1:]
    if word["tolkienian_word"].startswith("W"):
        word["tolkienian_word"] = "V" + word["tolkienian_word"][1:]
    w_pattern = r'(?<=[aeiou])(?<!ai)(?<!oi)w'
    if re.search(w_pattern, word["tolkienian_word"]):
        word["tolkienian_word"] = re.sub(w_pattern, 'v', word["tolkienian_word"])
    
    tengwar_info = word.get("tengwar")
    if tengwar_info is not None and tengwar_info != "w":
        word["tolkienian_word"] += f" [{tengwar_info}]"
        del word["tengwar"]
        return
       

def include_tengwar_info(word):
    if is_quenya(word):
        include_tengwar_info_for_quenya(word)
    else:
        tengwar_info = word.get("tengwar")
        if tengwar_info is not None:
            word["tolkienian_word"] += f" [{tengwar_info}]"
            del word["tengwar"]

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
    word_map["tengwar"] = word.get('tengwar')
    word_map["language"] = word.get('l')

    for key in word_map.keys():
        if word_map.get(key) is not None:
            word_map[key] = word_map[key].replace(DELIMITER, "")

    include_tengwar_info(word_map)

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

def field_exists_for_all_true_duplicates(duplicates, field, word_to_compare_to):
    for word in duplicates:
        if word["english_word"] != word_to_compare_to["english_word"]:
            continue
        if word["tolkienian_word"] != word_to_compare_to["tolkienian_word"]:
            continue
        if word.get(field) is None:
            return False
    return True

def add_uniqueness_via_field(duplicates, field):
    for word in duplicates:
        field_breaks_duplication = not is_field_same_for_all(duplicates, field)
        if field_breaks_duplication and field_exists_for_all_true_duplicates(duplicates, field, word):
            if word.get("extra_info") is None:
                word["extra_info"] = ""
            else:
                word["extra_info"] += ", "
            word["extra_info"] += word.get(field)

def invalidate_word(word):
    word["tolkienian_word"] = None
    word["english_word"] = None

def is_contained_in_variants(word, variant):
    if word == variant:
        return False
    MARKERS = ["*", "?", "⚠️"]
    MARKER_PATTERN = "[\*\?⚠️]"
    is_variant = "(" in variant and ")" in variant
    has_marker = any(marker in word for marker in MARKERS)
    if not is_variant and not has_marker:
        return False
    longer_variant = variant.replace("(", "").replace(")", "")
    shorter_variant = re.sub(r'\(.*?\)', '', variant)
    word_without_markers = re.sub(MARKER_PATTERN, '', word)
    return word_without_markers == longer_variant or word_without_markers == shorter_variant

def remove_duplicate_translations(words):
    deduped = words.copy()
    for word in words:
        for variant in words:
            if is_contained_in_variants(word, variant):
                deduped.remove(word)
    deduped = list(set(deduped))
    return deduped

def merge_duplicates(duplicates, field_to_merge):
    values_to_merge = [word.get(field_to_merge) for word in duplicates if word.get(field_to_merge) is not None]
    values_to_merge = remove_duplicate_translations(values_to_merge)
    values_to_merge.sort()

    merged_values = ""
    
    if len(values_to_merge) == 1:
        merged_values = values_to_merge[0]
    else:
        counter = 1
        for value in values_to_merge:
            if counter > 1:
                merged_values += "; "
            merged_values += f"({counter}) {value}"
            counter += 1
    
    for i in range(0, len(duplicates)):
        if i == 0:
            duplicates[i][field_to_merge] = merged_values
        else:
            invalidate_word(duplicates[i])

def make_tolkienian_duplicates_unique(duplicates):
    add_uniqueness_via_field(duplicates, "part_of_speech")
    duplicates = find_tolkienian_duplicates(duplicates, duplicates[0])
    add_uniqueness_via_field(duplicates, "category")
    duplicates = find_tolkienian_duplicates(duplicates, duplicates[0])

    if len(duplicates) > 1:
        merge_duplicates(duplicates, "english_word")

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
        if len(english_duplicates) > 1:
            merge_duplicates(english_duplicates, "tolkienian_word")
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
        language_name = "Neo-" + language_name
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
    print("Collected cards of the following part of speech types:\n", included_speech_values)

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
        print("Collected ", len(word_maps), " cards")

        formatted_words = format_words(word_maps)

        write_to_file(args, languages, formatted_words)
    else:
        raise ValueError("Could not read Eldamo data")

if __name__ == "__main__":
    args = parse_args()
    main(args)
