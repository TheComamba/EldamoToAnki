import argparse
import copy
import os
import re
import requests
import xml.etree.ElementTree as ElementTree

INPUT_URL = "https://github.com/pfstrack/eldamo/raw/master/src/data/eldamo-data.xml"
INPUT_FILE = "input/eldamo-data.xml"

SUPPORTED_LANGUAGES = []
ADUNAIC = { "id": "ad", "name": "Adunaic" }
SUPPORTED_LANGUAGES.append(ADUNAIC)
BLACK_SPEECH = { "id": "bs", "name": "Black-Speech" }
SUPPORTED_LANGUAGES.append(BLACK_SPEECH)
EARLY_NOLDORIN = { "id": "en", "name": "Early-Noldorin", "marker": "ᴱN" }
SUPPORTED_LANGUAGES.append(EARLY_NOLDORIN)
EARLY_QUENYA = { "id": "eq", "name": "Early-Quenya", "marker": "ᴱQ"}
SUPPORTED_LANGUAGES.append(EARLY_QUENYA)
GNOMISH = { "id": "g", "name": "Gnomish", "marker": "G" }
SUPPORTED_LANGUAGES.append(GNOMISH)
KHUZDUL = { "id": "kh", "name": "Khuzdul" }
SUPPORTED_LANGUAGES.append(KHUZDUL)
NOLDORIN = { "id": "n", "name": "Noldorin", "marker": "N"}
SUPPORTED_LANGUAGES.append(NOLDORIN)
PRIMITIVE = { "id": "p", "name": "Primitive" }
SUPPORTED_LANGUAGES.append(PRIMITIVE)
NEO_PRIMITIVE = { "id": "np", "name": "Neo-Primitive" }
SUPPORTED_LANGUAGES.append(NEO_PRIMITIVE)
MIDDLE_QUENYA = { "id": "mq", "name": "Middle-Quenya", "marker": "ᴹQ"}
SUPPORTED_LANGUAGES.append(MIDDLE_QUENYA)
QUENYA = { "id": "q", "name": "Quenya", "marker": "Q"}
SUPPORTED_LANGUAGES.append(QUENYA)
NEO_QUENYA = { "id": "nq", "name": "Neo-Quenya", "marker": "ᴺQ"}
SUPPORTED_LANGUAGES.append(NEO_QUENYA)
SINDARIN = { "id": "s", "name": "Sindarin", "marker": "S"}
SUPPORTED_LANGUAGES.append(SINDARIN)
NEO_SINDARIN = { "id": "ns", "name": "Neo-Sindarin", "marker": "ᴺS"}
SUPPORTED_LANGUAGES.append(NEO_SINDARIN)
TELERIN = { "id": "t", "name": "Telerin"}
SUPPORTED_LANGUAGES.append(TELERIN)

SPEECH_INDIVIDUAL_NAMES = ["fem-name", "masc-name", "place-name"]
SPEECH_COLLECTIVE_NAMES = "collective-name"
SPEECH_PROPER_NAMES = "proper-name"
SPEECH_PHRASES = "phrase"
SPEECH_EXCLUDES = ["grammar", "phoneme", "phonetic-rule", "phonetic-group", "phonetics", "root", "text", "?"]

DEFUNCT_VERBS= ["can", "could", "may", "might", "must", "ought", "quoth", "said", "says", "shall", "should", "would"]

DELIMITER = "|"
UNGLOSSED = "[unglossed]"

def parse_args():
    parser = argparse.ArgumentParser(description='Generate text files that are easily imported with Anki.')
    parser.add_argument('language', type=str, help='Language to generate')
    parser.add_argument('--neo', action='store_true', default=False, help='Assemble Neo-Eldarin lists, drawing from words invented by Tolkien throughout his life as well as fan-invented words')
    parser.add_argument('--individual-names', action='store_true', default=False, help='Include names of individuals and places')
    parser.add_argument('--collective-names', action='store_true', default=False, help='Include names for collective people')
    parser.add_argument('--proper-names', action='store_true', default=False, help='Include proper names')
    parser.add_argument('--phrases', action='store_true', default=False, help='Include phrases')
    parser.add_argument('--include-archaic', action='store_true', default=False, help='Include words marked as archaic')
    parser.add_argument('--include-origin', action='store_true', default=False, help='Include the linguistic origin of the word in the card')
    parser.add_argument('--include-deprecated', action='store_true', default=False, help='Include words that Paul Strack has marked as deprecated in neo lists')
    parser.add_argument('--check-for-updates', action='store_true', default=False, help='Forces a re-download of the Eldamo database')
    parser.add_argument('--verbose', action='store_true', default=False, help='Print more output')

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
    
    if args.neo:
        if languages[0] == PRIMITIVE:
            languages.append(NEO_PRIMITIVE)
        elif languages[0] == QUENYA:
            languages.append(NEO_QUENYA)
            languages.append(MIDDLE_QUENYA)
        elif languages[0] == SINDARIN:
            languages.append(NEO_SINDARIN)
            languages.append(NOLDORIN)
        else:
            raise ValueError(f"Neo lists are not supported for {languages[0]['name']}")
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
    if args.neo:
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
    is_eq = word.get('language') == EARLY_QUENYA.get('id')
    is_mq = word.get('language') == MIDDLE_QUENYA.get('id')
    is_q = word.get('language') == QUENYA.get('id')
    is_nq = word.get('language') == NEO_QUENYA.get('id')
    return is_eq or is_mq or is_q or is_nq

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
       
def remove_origin_marker(word):
    for language in SUPPORTED_LANGUAGES:
        marker = language.get('marker')
        if marker is not None:
            full_marker = f"[{marker}.] "
            word["english_word"] = word["english_word"].replace(full_marker, "")
            full_marker = f"[{marker}.]"
            word["english_word"] = word["english_word"].replace(full_marker, "")

def include_stem_info(word):
    tengwar_info = word.get("stem")
    if tengwar_info is not None:
        word["tolkienian_word"] += f" ({tengwar_info})"
        del word["stem"]

def include_tengwar_info(word):
    if is_quenya(word):
        include_tengwar_info_for_quenya(word)
    else:
        tengwar_info = word.get("tengwar")
        if tengwar_info is not None:
            word["tolkienian_word"] += f" [{tengwar_info}]"
            del word["tengwar"]

def normalise_quenya_spelling(word):
    patterns = [
        (r'kw', 'qu'),
        (r'Kw', 'Qu'),
        (r'ks', 'x'),
        (r'Ks', 'X'),
        (r'ea', 'ëa'),
        (r'eo', 'ëo'),
        (r'ie', 'ië'),
        (r'oa', 'öa'),
        (r'Ea', 'Ëa'),
        (r'Eo', 'Ëo'),
        (r'Ie', 'Ië'),
        (r'Oa', 'Öa'),
        (r'eä', 'ëa'),
        (r'eö', 'ëo'),
        (r'ïe', 'ië'),
        (r'oä', 'öa'),
        (r'Eä', 'Ëa'),
        (r'Eö', 'Ëo'),
        (r'Ïe', 'Ië'),
        (r'Oä', 'Öa'),
        (r'k(?![ws])', 'c'),
        (r'K(?![ws])', 'C'),
        (r'q(?![u])', 'qu'),
        (r'Q(?![u])', 'Qu'),
        (r'e(?=\s|$)', 'ë'),
    ]
    for pattern in patterns:
        if re.search(pattern[0], word["tolkienian_word"]):
            word["tolkienian_word"] = re.sub(pattern[0], pattern[1], word["tolkienian_word"])

def remove_translations_after_marker(word, marker):
    if marker in word["english_word"]:
        index = word["english_word"].find(marker)
        word["english_word"] = word["english_word"][:index]
    
    word["english_word"] = word["english_word"].strip()
    
    if word["english_word"].endswith(',') or word["english_word"].endswith(';'):
        word["english_word"] = word["english_word"][:-1].strip()

def remove_deprecated_translations(word):
    remove_translations_after_marker(word, '⚠️')

def remove_archaic_translations(word):
    remove_translations_after_marker(word, '†')

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

def word_to_map(all_words, word, categories, args):
    word_map = {}
    word_map["tolkienian_word"] = word.get('v')
    if word_map.get("tolkienian_word") is None:
        if args.verbose:
            print("Skipping word without value: ")
            debug_print_word(word)
        return None
    word_map["english_word"] = find_translation(all_words, word, args)
    if word_map.get("english_word") is None:
        if args.verbose:
            print("Skipping word without translation: ", word_map.get("tolkienian_word"))
        return None
    word_map["english_word"] = word_map["english_word"].replace("&", "and")
    word_map["part_of_speech"] = word.get('speech')
    word_map["stem"] = word.get('stem')
    word_map["category"] = get_category(word, categories)
    word_map["tengwar"] = word.get('tengwar')
    word_map["language"] = word.get('l')

    for key in word_map.keys():
        if word_map.get(key) is not None:
            word_map[key] = word_map[key].replace(DELIMITER, "")

    if args.neo:
        if not args.include_deprecated:
            remove_deprecated_translations(word_map)
        if not args.include_origin:
            remove_origin_marker(word_map)
    if not args.include_archaic:
        remove_archaic_translations(word_map)

    remove_duplication_marker(word_map)

    include_stem_info(word_map)
    
    include_tengwar_info(word_map)

    if is_quenya(word_map):
        normalise_quenya_spelling(word_map)

    return word_map

def split_string_outside_parenthesis(string):
    parts = []
    temp = ""
    depth = 0

    for char in string:
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char in ",;" and depth == 0:
            if temp:
                parts.append(temp)
                temp = ""
            continue
        temp += char

    if temp:
        parts.append(temp)

    return parts

def split_word_map(word_map):
    maps = []
    english_words = split_string_outside_parenthesis(word_map["english_word"])
    for english_word in english_words:
        new_map = copy.deepcopy(word_map)
        english_word = english_word.strip()
        if needs_added_to(word_map, english_word):
            english_word = "to " + english_word
            english_word = english_word.replace("to (lit.)", "(lit.) to")
            english_word = english_word.replace("to (orig.)", "(orig.) to")
        new_map["english_word"] = english_word
        maps.append(new_map)
    return maps

def needs_added_to(word_map, english_word):
    if not word_map.get("part_of_speech") == "vb":
        return False
    if english_word.startswith("to "):
        return False
    starts_with_non_alphanumeric_and_then_to = bool(re.match(r"^(?:[^a-zA-Z]?to )", english_word))
    if starts_with_non_alphanumeric_and_then_to:
        return False
    if english_word.startswith("(lit.) to"):
        return False
    if english_word.startswith("(orig.) to"):
        return False
    if english_word in DEFUNCT_VERBS:
        return False
    return True
    
def words_to_maps(words, categories, args):
    word_maps = []
    for word in words:
        word_map = word_to_map(words, word, categories, args)
        if word_map is not None:
            split_maps = split_word_map(word_map)
            word_maps.extend(split_maps)
    return word_maps

def find_tolkienian_duplicates(all_words, word_input):
    duplicates = []
    for word_iter in all_words:
        if are_tolkienian_duplicates(word_input, word_iter):
            duplicates.append(word_iter)
    return duplicates

def are_tolkienian_duplicates(word1, word2):
    if word1.get("tolkienian_word") is None or word2.get("tolkienian_word") is None:
        return False
    if word1.get("extra_info") != word2.get("extra_info"):
        return False
    tw1 = word1.get("tolkienian_word")
    tw2 = word2.get("tolkienian_word")
    if tw1 == tw2:
        return True
    else:
        return False

def find_english_duplicates(all_words, word_input):
    duplicates = []
    for word_iter in all_words:
        if are_english_duplicates(word_input, word_iter):
            duplicates.append(word_iter)
    return duplicates
    
def are_english_duplicates(word1, word2):
    if word1.get("english_word") is None or word2.get("english_word") is None:
        return False
    if word1.get("part_of_speech") != word2.get("part_of_speech"):
        return False
    ew1 = word1.get("english_word")
    ew2 = word2.get("english_word")
    UNCERTAINTY_MARKERS = ["*", "?"]
    for marker in UNCERTAINTY_MARKERS:
        ew1 = ew1.replace(marker, "")
        ew2 = ew2.replace(marker, "")
    if ew1 == ew2:
        return True
    else:
        return False

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

    MARKERS = ["*", "?"]
    MARKER_PATTERN = "[\*\?]"
    DIACRITIC_REPLACEMENTS = [
        ("â", "á"),
        ("Â", "Á"),
        ("ê", "é"),
        ("Ê", "É"),
        ("î", "í"),
        ("Î", "Í"),
        ("ô", "ó"),
        ("Ô", "Ó"),
        ("û", "ú"),
        ("Û", "Ú"),
        ("ŷ", "ý"),
        ("Ŷ", "Ý"),
        ("ä", "a"),
        ("Ä", "A"),
        ("ë", "e"),
        ("Ë", "E"),
        ("ï", "i"),
        ("Ï", "I"),
        ("ö", "o"),
        ("Ö", "O"),
        ("ü", "u"),
        ("Ü", "U"),
        ("ÿ", "y"),
        ("Ÿ", "Y")
    ]
    is_variant = "(" in variant and ")" in variant
    has_marker = any(marker in word for marker in MARKERS)
    has_diacritic = any(diacritic[0] in variant for diacritic in DIACRITIC_REPLACEMENTS)
    wordContainsUppercase = word != word.lower()
    variantContainsUppercase = variant != variant.lower()
    casingIsDifferent = wordContainsUppercase != variantContainsUppercase
    if not is_variant and not has_marker and not has_diacritic and not casingIsDifferent:
        return False
    
    if casingIsDifferent:
        variant = variant.lower()

    if has_diacritic:
        for diacritic in DIACRITIC_REPLACEMENTS:
            word = word.replace(diacritic[0], diacritic[1])
            variant = variant.replace(diacritic[0], diacritic[1])
    
    if has_marker:
        word = re.sub(MARKER_PATTERN, '', word)
    
    if is_variant:
        longer_variant = variant.replace("(", "").replace(")", "")
        shorter_variant = re.sub(r'\(.*?\)', '', variant).strip()
        return word == longer_variant or word == shorter_variant
    else:
        return word == variant

def translations_sorter(x):
    SORTED_MARKERS = ['!', '*', '?', '†', '(lit.)', '(orig.)']
    primary_sorting_criterium = 0
    for (index, marker) in enumerate(SORTED_MARKERS):
        if marker in x:
            primary_sorting_criterium = index + 1
    return (primary_sorting_criterium, x)

def remove_duplicate_translations(words):
    deduped = words.copy()
    for word in words:
        for variant in words:
            if is_contained_in_variants(word, variant) and word in deduped:
                deduped.remove(word)
    deduped = list(set(deduped))
    deduped.sort(key=translations_sorter)
    return deduped

def merge_duplicates(duplicates, field_to_merge):
    values_to_merge = [word.get(field_to_merge) for word in duplicates if word.get(field_to_merge) is not None]
    values_to_merge = remove_duplicate_translations(values_to_merge)

    merged_values = "; ".join(values_to_merge)
    
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

def is_extra_info_necessary(word_with_extra_info, all_words):
    duplicates = [word for word in all_words if word.get("tolkienian_word") == word_with_extra_info.get("tolkienian_word")]
    duplicates = [word for word in duplicates if word.get("english_word") != word_with_extra_info.get("english_word")]
    return len(duplicates) > 0

def remove_unnecessary_extra_info(all_words):
    for word in all_words:
        hasExtraInfo = word.get("extra_info") is not None
        if hasExtraInfo and not is_extra_info_necessary(word, all_words):
            word["extra_info"] = None

def remove_duplications(all_words):
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
    remove_unnecessary_extra_info(all_words)
    return all_words

def format_word(word):
    tolkienian = word.get("tolkienian_word")
    extra_info = word.get("extra_info")
    english = word.get("english_word")
    part_of_speech = word.get("part_of_speech")

    formatted_word = f"{tolkienian}"
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
    if args.neo:
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

def is_deprecated(word, all_words, referenced_words=[]):
    """
    This is the relevant part for the logic:
    https://github.com/pfstrack/eldamo/blob/master/src/main/webapp/config/query-configs/root-index.xq
    """
    if word.find('deprecated') is not None:
        return True
    if word.get('mark') == "|":
        return True
    if word.get('mark') == "-":
        return True
    if word.get('mark') == "‽":
        return True
    ref = word.find('see')
    if ref is not None:
        value = word.get('v')
        if value is None:
            return False
        if value in referenced_words:
            print("Circular reference detected: ", referenced_words)
            return False
        referenced_words.append(value)
        for word_iter in all_words:
            ref_value = ref.get('v')
            ref_language = ref.get('l')
            iter_value = word_iter.get('v')
            iter_language = word_iter.get('l')
            if iter_value == ref_value and iter_language == ref_language:
                return is_deprecated(word_iter, all_words, referenced_words)
    return False

def is_archaic(word):
    return word.get('mark') == "†"

def filtered_words(args, language_ids, speech_types_to_exclude, words):
    filtered = [word for word in words if word.get('l') in language_ids]
    if args.neo and not args.include_deprecated:
        filtered = [word for word in filtered if not is_deprecated(word, filtered, [])]
    if not args.include_archaic:
        filtered = [word for word in filtered if not is_archaic(word)]
    filtered = [word for word in filtered if word.get('speech') not in speech_types_to_exclude]
    return filtered

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
        
        filtered = filtered_words(args, language_ids, speech_types_to_exclude, words)
        
        if args.verbose:
            print_parts_of_speech(filtered)

        word_maps = words_to_maps(filtered, categories, args)

        word_maps = remove_duplications(word_maps)
        if args.verbose:
            print("Collected ", len(word_maps), " cards")

        formatted_words = format_words(word_maps)

        write_to_file(args, languages, formatted_words)
    else:
        raise ValueError("Could not read Eldamo data")

if __name__ == "__main__":
    args = parse_args()
    main(args)
