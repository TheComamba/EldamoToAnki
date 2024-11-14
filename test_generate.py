import unittest
from types import SimpleNamespace
import xml.etree.ElementTree as ET
from generate import add_uniqueness_via_field, are_english_duplicates, are_tolkienian_duplicates, filtered_words, format_word, format_words, include_tengwar_info, make_tolkienian_duplicates_unique, merge_duplicates, normalise_quenya_spelling, parse_args, remove_deprecated_translations, remove_duplicate_translations, main, remove_duplications, remove_origin_marker, split_word_map, words_to_maps

def dict_to_xml(tag, d):
    elem = ET.Element(tag)
    for key, val in d.items():
        if isinstance(val, dict):
            elem.append(dict_to_xml(key, val))
        elif isinstance(val, list):
            for subdict in val:
                elem.append(dict_to_xml(key, subdict))
        else:
            elem.set(key, str(val))
    return elem

def list_to_xml(list):
    root = ET.Element("words")
    for d in list:
        root.append(dict_to_xml("word", d))
    return ET.ElementTree(root)

class TestGenerate(unittest.TestCase):
    def test_include_tengwar_info(self):
        word = {"tolkienian_word": "mísë", "tengwar": "þ"}
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "mísë [þ]")

    def test_include_tengwar_info_for_any_language(self):
        word = {"language": "s", "tolkienian_word": "gaur", "tengwar": "ng-"}
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "gaur [ng-]")
    
    def test_do_not_include_tengwar_info_for_quenya_w(self):
        word = {"language": "q", "tolkienian_word": "vingë", "tengwar": "w"}
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "vingë")

    def test_include_implicit_tengwar_info_for_thule(self):
        word = {"language": "q", "tolkienian_word": "míþë"}
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "mísë [þ]")
    
    def test_include_implicit_tengwar_info_for_w(self):
        word = {"language": "q", "tolkienian_word": "wilya"} # Replaced at beginning of word
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "vilya") # No mention of the original spelling

        word = {"language": "q", "tolkienian_word": "Wilya"} # Also works for capital letter
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "Vilya")

        word = {"language": "q", "tolkienian_word": "awalda"} # Replaced after vowel
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "avalda")

        word = {"language": "q", "tolkienian_word": "aiwendil"} # Not replaced after ai
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "aiwendil")

        word = {"language": "q", "tolkienian_word": "oiwa"} # Not replaced after oi
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "oiwa")

        word = {"language": "q", "tolkienian_word": "inwe"} # Not replaced after consonant
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "inwe")

    def test_include_implicit_tengwar_info_for_initial_ng(self):
        word = {"language": "q", "tolkienian_word": "ñauna-"}
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "nauna- [ñ-]")

        word = {"language": "q", "tolkienian_word": "Ñoldo"}
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "Noldo [ñ-]")

    def test_include_implicit_tengwar_info_operates_on_neo_quenya(self):
        word = {"language": "nq", "tolkienian_word": "míþë"}
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "mísë [þ]")

    def test_include_implicit_tengwar_info_only_operates_on_quenya(self):
        word = {"language": "t", "tolkienian_word": "þarma"}
        include_tengwar_info(word)
        self.assertEqual(word["tolkienian_word"], "þarma")

    def test_removing_deprecated_translation(self):
        word = {"tolkienian_word": "céva", "english_word": "fresh, new, ⚠️renewed"}
        remove_deprecated_translations(word)
        self.assertEqual(word["english_word"], "fresh, new")

        word = {"tolkienian_word": "curu", "english_word": "skill; ⚠️[ᴱQ.] magic, wizardry"}
        remove_deprecated_translations(word)
        self.assertEqual(word["english_word"], "skill")

    def test_removing_origin_marker(self):
        word = {"tolkienian_word": "curu", "english_word": "skill; [ᴱQ.] magic, wizardry"}
        remove_origin_marker(word)
        self.assertEqual(word["english_word"], "skill; magic, wizardry")

    def test_normalise_quenya_spelling(self):
        word = {"language": "q", "tolkienian_word": "aksa akwa aka aqa aqua"}
        normalise_quenya_spelling(word)
        self.assertEqual(word["tolkienian_word"], "axa aqua aca aqua aqua")

        word = {"language": "q", "tolkienian_word": "Ksa Kwa Ka Qa Qua"}
        normalise_quenya_spelling(word)
        self.assertEqual(word["tolkienian_word"], "Xa Qua Ca Qua Qua")

        word = {"language": "q", "tolkienian_word": "(e)vilye"}
        normalise_quenya_spelling(word)
        self.assertEqual(word["tolkienian_word"], "(e)vilyë")

        word = {"language": "q", "tolkienian_word": "ea eo ie oa Ea Eo Ie Oa"}
        normalise_quenya_spelling(word)
        self.assertEqual(word["tolkienian_word"], "ëa ëo ië öa Ëa Ëo Ië Öa")

        word = {"language": "q", "tolkienian_word": "eä eö ïe oä Eä Eö Ïe Oä"}
        normalise_quenya_spelling(word)
        self.assertEqual(word["tolkienian_word"], "ëa ëo ië öa Ëa Ëo Ië Öa")

    def test_words_are_tolkienian_duplicates(self):
        word = {"tolkienian_word": "tolkienian", "english_word": "english", "extra_info": "extra", "part_of_speech": "n"}

        no_tolkienian = word.copy()
        no_tolkienian["tolkienian_word"] = None
        self.assertFalse(are_tolkienian_duplicates(word, no_tolkienian))

        other_tolkienian = word.copy()
        other_tolkienian["tolkienian_word"] = "other"
        self.assertFalse(are_tolkienian_duplicates(word, other_tolkienian))

        other_english = word.copy()
        other_english["english_word"] = "other"
        self.assertTrue(are_tolkienian_duplicates(word, other_english))

        other_extra = word.copy()
        other_extra["extra_info"] = "other"
        self.assertFalse(are_tolkienian_duplicates(word, other_extra))

        other_pos = word.copy()
        other_pos["part_of_speech"] = "other"
        self.assertTrue(are_tolkienian_duplicates(word, other_pos))

    def test_words_are_english_duplicates(self):
        word = {"tolkienian_word": "tolkienian", "english_word": "english", "extra_info": "extra", "part_of_speech": "n"}

        no_english = word.copy()
        no_english["english_word"] = None
        self.assertFalse(are_english_duplicates(word, no_english))

        other_tolkienian = word.copy()
        other_tolkienian["tolkienian_word"] = "other"
        self.assertTrue(are_english_duplicates(word, other_tolkienian))

        other_english = word.copy()
        other_english["english_word"] = "other"
        self.assertFalse(are_english_duplicates(word, other_english))

        other_extra = word.copy()
        other_extra["extra_info"] = "other"
        self.assertTrue(are_english_duplicates(word, other_extra))

        other_pos = word.copy()
        other_pos["part_of_speech"] = "other"
        self.assertFalse(are_english_duplicates(word, other_pos))
    
    def test_invalid_words_are_not_duplicates(self):
        word = {"tolkienian_word": None, "english_word": None, "stem": "stem", "extra_info": "extra", "part_of_speech": "n"}

        self.assertFalse(are_tolkienian_duplicates(word, word))
        self.assertFalse(are_english_duplicates(word, word))

    def test_adding_uniqueness_via_field_with_all_the_same_adds_nothing(self):
        words = [
            {"tolkienian_word": "sívë", "english_word": "knowing", "test": "test"},
            {"tolkienian_word": "sívë", "english_word": "peace", "test": "test"},
            {"tolkienian_word": "sívë", "english_word": "as", "test": "test"},
        ]
        add_uniqueness_via_field(words, "test")
        for word in words:
            self.assertNotIn("extra_info", word)
    
    def test_adding_uniqueness_via_field_with_one_deviant_adds_to_all(self):
        words = [
            {"tolkienian_word": "sívë", "english_word": "knowing", "test": "test"},
            {"tolkienian_word": "sívë", "english_word": "peace", "test": "test"},
            {"tolkienian_word": "sívë", "english_word": "as", "test": "noodle"},
        ]
        add_uniqueness_via_field(words, "test")
        self.assertEqual(words[0]["extra_info"], "test")
        self.assertEqual(words[1]["extra_info"], "test")
        self.assertEqual(words[2]["extra_info"], "noodle")
    
    def test_remove_duplicate_translations_with_asterisk(self):
        words = ["bla", "*bla"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["bla"])

    def test_remove_duplicate_translations_with_question_mark(self):
        words = ["bla", "?bla"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["bla"])

    def test_remove_duplicate_translations_with_accent(self):
        words = ["â", "á", "a"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["a", "â"])

        words = ["Â", "Á", "A"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["A", "Â"])

        words = ["ê", "é", "e"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["e", "ê"])

        words = ["Ê", "É", "E"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["E", "Ê"])

        words = ["î", "í", "i"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["i", "î"])

        words = ["Î", "Í", "I"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["I", "Î"])

        words = ["ô", "ó", "o"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["o", "ô"])

        words = ["Ô", "Ó", "O"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["O", "Ô"])

        words = ["û", "ú", "u"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["u", "û"])

        words = ["Û", "Ú", "U"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["U", "Û"])

        words = ["ŷ", "ý", "y"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["y", "ŷ"])

        words = ["Ŷ", "Ý", "Y"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["Y", "Ŷ"])

    def test_remove_duplicate_translations_with_trema(self):
        words = ["ä", "a"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["ä"])

        words = ["Ä", "A"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["Ä"])

        words = ["ë", "e"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["ë"])

        words = ["Ë", "E"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["Ë"])

        words = ["ï", "i"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["ï"])

        words = ["Ï", "I"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["Ï"])

        words = ["ö", "o"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["ö"])

        words = ["Ö", "O"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["Ö"])

        words = ["ü", "u"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["ü"])

        words = ["Ü", "U"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["Ü"])

        words = ["ÿ", "y"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["ÿ"])

        words = ["Ÿ", "Y"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["Ÿ"])

    def test_remove_case_insensitive_duplicate_translations(self):
        words = ["autumn", "Autumn"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["Autumn"])

    def test_remove_parenthesis_duplicate_translations(self):
        words = ["l(h)ô", "lô"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["l(h)ô"])

    def test_remove_parenthesis_and_space_duplicate_translations(self):
        words = ["end", "(the) end"]
        deduped = remove_duplicate_translations(words)
        self.assertEqual(deduped, ["(the) end"])

    def test_merging_tolkienian_duplicates(self):
        words = [
            {"tolkienian_word": "sívë", "english_word": "knowing"},
            {"tolkienian_word": "sívë", "english_word": "peace"},
            {"tolkienian_word": "sívë", "english_word": "as"},
        ]
        merge_duplicates(words, "english_word")
        self.assertEqual(words[0]["english_word"], "as; knowing; peace")
        self.assertIsNone(words[1]["english_word"])
        self.assertIsNone(words[2]["english_word"])

    def test_lit_is_at_the_end_when_merging_duplicates(self):
        words = [
            {"tolkienian_word": "Anarya", "english_word": "Sunday"},
            {"tolkienian_word": "Anarya", "english_word": "(lit.) Sun-day"},
        ]
        merge_duplicates(words, "english_word")
        self.assertEqual(words[0]["english_word"], "Sunday; (lit.) Sun-day")

    def test_orig_is_at_the_end_when_merging_duplicates(self):
        words = [
            {"tolkienian_word": "Anarya", "english_word": "Sunday"},
            {"tolkienian_word": "Anarya", "english_word": "(orig.) Sun-day"},
        ]
        merge_duplicates(words, "english_word")
        self.assertEqual(words[0]["english_word"], "Sunday; (orig.) Sun-day")

    def test_non_alphabeticals_are_at_the_end_when_merging_duplicates(self):
        words = [
            {"tolkienian_word": "Anarya", "english_word": "(lit.) ice-drop"},
            {"tolkienian_word": "Anarya", "english_word": "*icicle"},
            {"tolkienian_word": "Anarya", "english_word": "icy-ice-ice"},
        ]
        merge_duplicates(words, "english_word")
        self.assertEqual(words[0]["english_word"], "icy-ice-ice; *icicle; (lit.) ice-drop")

    def test_merging_tolkienian_true_duplicates(self):
        words = [
            {"tolkienian_word": "cenya", "english_word": "*seeing"},
            {"tolkienian_word": "cenya", "english_word": "*seeing"},
        ]
        merge_duplicates(words, "english_word")
        self.assertEqual(words[0]["english_word"], "*seeing")
        self.assertIsNone(words[1]["english_word"])
    
    def test_merging_duplicates_with_provided_alternatives(self):
        words = [
            {"tolkienian_word": "(a)lá", "english_word": "yes"},
            {"tolkienian_word": "lá", "english_word": "yes"},
            {"tolkienian_word": "alá", "english_word": "yes"},
        ]
        merge_duplicates(words, "tolkienian_word")
        self.assertEqual(words[0]["tolkienian_word"], "(a)lá")
        self.assertIsNone(words[1]["tolkienian_word"])

    def test_merging_duplicates_with_some_provided_alternatives(self):
        words = [
            {"tolkienian_word": "(a)lá", "english_word": "yes"},
            {"tolkienian_word": "lá", "english_word": "yes"},
            {"tolkienian_word": "alá", "english_word": "yes"},
            {"tolkienian_word": "test", "english_word": "yes"},
        ]
        merge_duplicates(words, "tolkienian_word")
        self.assertEqual(words[0]["tolkienian_word"], "(a)lá; test")
        self.assertIsNone(words[1]["tolkienian_word"])
        self.assertIsNone(words[2]["tolkienian_word"])

    def test_make_tolkienian_duplicates_unique_does_add_extra_info_for_duplicates(self):
        words = [
            {"tolkienian_word": "gaer", "english_word": "awful", "category": "Emotion"},
            {"tolkienian_word": "gaer", "english_word": "red"},
        ]
        make_tolkienian_duplicates_unique(words)
        self.assertEqual(words[0]["extra_info"], "Emotion")
        self.assertNotIn("extra_info", words[1])

    def test_make_tolkienian_duplicates_unique_does_not_add_extra_info_for_true_duplicates(self):
        words = [
            {"tolkienian_word": "cenya", "english_word": "*seeing", "category": "Sense Perception"},
            {"tolkienian_word": "cenya", "english_word": "*seeing"},
        ]
        make_tolkienian_duplicates_unique(words)
        self.assertNotIn("extra_info", words[0])
        self.assertNotIn("extra_info", words[1])
    
    def test_words_with_several_translations_are_split_at_comma_or_semicolon(self):
        words = {"tolkienian_word": "sívë", "english_word": "knowing, peace; as", "test": "test"}
        maps = split_word_map(words)
        self.assertEqual(len(maps), 3)
        self.assertEqual(maps[0]["english_word"], "knowing")
        self.assertEqual(maps[0]["test"], "test")
        self.assertEqual(maps[1]["english_word"], "peace")
        self.assertEqual(maps[1]["test"], "test")
        self.assertEqual(maps[2]["english_word"], "as")
        self.assertEqual(maps[2]["test"], "test")

    def test_verbs_with_several_translations_get_to_prepended(self):
        words = {"tolkienian_word": "gwathra", "english_word": "to dim, obscure", "part_of_speech": "vb"}
        maps = split_word_map(words)
        self.assertEqual(len(maps), 2)
        self.assertEqual(maps[0]["english_word"], "to dim")
        self.assertEqual(maps[1]["english_word"], "to obscure")

    def test_to_prepending_respects_markers(self):
        words = {"tolkienian_word": "bla", "english_word": "to be, *to not be, €to something, (lit.) to verily exist", "part_of_speech": "vb"}
        maps = split_word_map(words)
        self.assertEqual(len(maps), 4)
        self.assertEqual(maps[0]["english_word"], "to be")
        self.assertEqual(maps[1]["english_word"], "*to not be")
        self.assertEqual(maps[2]["english_word"], "€to something")
        self.assertEqual(maps[3]["english_word"], "(lit.) to verily exist")

    def test_to_is_not_prepended_for_defective_verbs(self):
        words = {"tolkienian_word": "bla", "english_word": "can, could, may, might, must, ought, quoth, said, says, shall, should, would", "part_of_speech": "vb"}
        maps = split_word_map(words)
        self.assertEqual(maps[0]["english_word"], "can")
        self.assertEqual(maps[1]["english_word"], "could")
        self.assertEqual(maps[2]["english_word"], "may")
        self.assertEqual(maps[3]["english_word"], "might")
        self.assertEqual(maps[4]["english_word"], "must")
        self.assertEqual(maps[5]["english_word"], "ought")
        self.assertEqual(maps[6]["english_word"], "quoth")
        self.assertEqual(maps[7]["english_word"], "said")
        self.assertEqual(maps[8]["english_word"], "says")
        self.assertEqual(maps[9]["english_word"], "shall")
        self.assertEqual(maps[10]["english_word"], "should")
        self.assertEqual(maps[11]["english_word"], "would")

    def test_to_prepending_preserves_lit_at_front(self):
        words = {"tolkienian_word": "bla", "english_word": "(lit.) bla", "part_of_speech": "vb"}
        maps = split_word_map(words)
        self.assertEqual(len(maps), 1)
        self.assertEqual(maps[0]["english_word"], "(lit.) to bla")

    def test_to_prepending_preserves_orig_at_front(self):
        words = {"tolkienian_word": "bla", "english_word": "(orig.) bla", "part_of_speech": "vb"}
        maps = split_word_map(words)
        self.assertEqual(len(maps), 1)
        self.assertEqual(maps[0]["english_word"], "(orig.) to bla")

    def test_words_are_only_split_outside_parenthesis(self):
        words = {"tolkienian_word": "cólima", "english_word": "bearable, light (of burdens and things comparable, troubles, labors, afflications)"}
        maps = split_word_map(words)
        self.assertEqual(len(maps), 2)
        self.assertEqual(maps[0]["english_word"], "bearable")
        self.assertEqual(maps[1]["english_word"], "light (of burdens and things comparable, troubles, labors, afflications)")

        words = {"tolkienian_word": "test", "english_word": "test1, test2 [test3, test4]"}
        maps = split_word_map(words)
        self.assertEqual(len(maps), 2)
        self.assertEqual(maps[0]["english_word"], "test1")
        self.assertEqual(maps[1]["english_word"], "test2 [test3, test4]")

    def test_words_with_several_translations_are_split_at_comma_or_semicolon(self):
        words = [
            {"v": "sívë", "gloss": "knowing, peace; as"},
        ]
        categories = []
        args = SimpleNamespace(verbose=False, neo=False)
        maps = words_to_maps(words, categories, args)
        self.assertEqual(len(maps), 3)
        self.assertEqual(maps[0]["english_word"], "knowing")
        self.assertEqual(maps[1]["english_word"], "peace")
        self.assertEqual(maps[2]["english_word"], "as")
    
    def test_stem_is_added(self):
        words = [
            {"v": "Narquelion", "gloss": "Autumn", "stem": "Narqeliond-"},
        ]
        categories = []
        args = SimpleNamespace(verbose=False, neo=False)
        maps = words_to_maps(words, categories, args)
        self.assertEqual(len(maps), 1)
        self.assertEqual(maps[0]["tolkienian_word"], "Narquelion (Narqeliond-)")

    def test_spelling_is_normalised_also_for_stem(self):
        words = [
            {"v": "serke", "gloss": "blood", "stem": "serki-", "l": "q"},
        ]
        categories = []
        args = SimpleNamespace(verbose=False, neo=False)
        maps = words_to_maps(words, categories, args)
        self.assertEqual(len(maps), 1)
        self.assertEqual(maps[0]["tolkienian_word"], "sercë (serci-)")

    def test_formatting_simple_word(self):
        word = {"tolkienian_word": "hîr", "english_word": "lord"}
        formatted = format_word(word)
        self.assertEqual(formatted, "hîr|lord\n")
    
    def test_formatting_word_with_extra_info(self):
        word = {"tolkienian_word": "hîr", "english_word": "lord", "extra_info": "extra"}
        formatted = format_word(word)
        self.assertEqual(formatted, "hîr (extra)|lord\n")
    
    def test_formatting_word_with_part_of_speech(self):
        word = {"tolkienian_word": "hîr", "english_word": "lord", "part_of_speech": "n"}
        formatted = format_word(word)
        self.assertEqual(formatted, "hîr|lord (n)\n")

    def test_formatting_word_with_all(self):
        word = {"tolkienian_word": "mísë", "english_word": "grey", "extra_info": "extra", "part_of_speech": "adj"}
        formatted = format_word(word)
        self.assertEqual(formatted, "mísë (extra)|grey (adj)\n")

    def test_generating_sindarin_does_not_throw(self):
        args = parse_args()
        args.language = 'sindarin'
        main(args)
    
    def test_imbe(self):
        words = [
            {"l": "eq", "v": "imbe", "speech": "n", "gloss": "hive", "cat": "AN_BE"},
            {"l": "q", "v": "imbë¹", "speech": "prep adv", "gloss": "between, among"},
            {"l": "mq", "v": "imbe¹", "speech": "adv", "gloss": "in(wards)"},
            {"l": "q", "v": "imbë²", "speech": "n", "ngloss": "deep valley, (wide) ravine, [ᴹQ.] glen, dell, (lit.) tween-land", "cat": "PW_VA"},
            {"l": "mq", "v": "imbe²", "speech": "n", "gloss": "dell, deep vale, ravine, glen", "cat": "PW_VA"},
            {"l": "nq", "v": "nieres", "speech": "n", "gloss": "hive"},
        ]
        categories = [{"id": "AN", "label": "Animals"}, {"id": "PW", "label": "Physical World"}]
        args = SimpleNamespace(verbose=False, neo=True, language='quenya', include_deprecated=False, include_origin=False)
        root = list_to_xml(words)
        words = root.findall(".//word")
        maps = words_to_maps(words, categories, args)
        maps = remove_duplications(maps)
        formatted = format_words(maps)

        expected = [
            "imbë (adv)|in(wards) (adv)\n",
            "imbë (n, Physical World)|(wide) ravine; deep vale; deep valley; dell; glen; (lit.) tween-land (n)\n",
            "imbë (prep adv)|among; between (prep adv)\n",
            "imbë; niëres|hive (n)\n",
        ]

        self.assertEqual(formatted, expected)
    
    def test_one_ninth(self):
        root = ET.Element("words")
        huestya = dict_to_xml("word", {
            "l": "eq", "v": "huest(y)a", "speech": "adj", "gloss": "one ninth", 
                "deprecated": {
                    "l": "q", "v": "ne(re)sta"
                    }
            })
        huetya = dict_to_xml("word", {
            "l": "eq", "v": "huetya", "speech": "adj", "gloss": "one ninth",
                "see": {
                        "l": "eq", "v": "huest(y)a"
                        }
            })
        huestya.append(huetya)
        neresta = dict_to_xml("word", {
            "l": "q", "v": "ne(re)sta", "speech": "fraction", "gloss": "one ninth"
            })
        huesto = dict_to_xml("word", {
            "l": "eq", "v": "huesto", "speech": "fraction", "gloss": "one ninth",
                    "deprecated": {
                            "l": "q", "v": "ne(re)sta"
                                }
        })
        huetto = dict_to_xml("word", {
            "l": "eq", "v": "huetto", "speech": "fraction", "gloss": "one ninth",
                "see": {
                        "l": "eq", "v": "huesto"
                    }
        })
        huesto.append(huetto)
        neresta.append(huesto)
        nersat = dict_to_xml("word", {
            "l": "q", "v": "nersat", "speech": "fraction", "gloss": "one ninth",
                    "deprecated": {
                            "l": "q", "v": "ne(re)sta"
                            }
        })
        neresta.append(nersat)
        root.append(huestya)
        root.append(neresta)

        words = root.findall(".//word")
        self.assertEqual(len(words), 6)

        args = SimpleNamespace(verbose=False, neo=True, language='quenya', include_deprecated=False, include_origin=False)
        language_ids = ["eq", "mq", "q", "nq"]
        speech_types_to_exclude = []
        categories = []
        filtered = filtered_words(args, language_ids, speech_types_to_exclude, words)
        maps = words_to_maps(filtered, categories, args)
        formatted = format_words(maps)

        expected = [
            "ne(re)sta|one ninth (fraction)\n"
        ]

        self.assertEqual(formatted, expected)

if __name__ == '__main__':
    unittest.main()
