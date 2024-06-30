import unittest
from generate import add_uniqueness_via_field, are_english_duplicates, are_tolkienian_duplicates, format_word, include_tengwar_info, make_tolkienian_duplicates_unique, merge_duplicates, normalise_quenya_spelling, parse_args, remove_deprecated_translations, remove_duplicate_translations, main, remove_origin_marker

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

    def test_words_are_tolkienian_duplicates(self):
        word = {"tolkienian_word": "tolkienian", "english_word": "english", "stem": "stem", "extra_info": "extra", "part_of_speech": "n"}

        no_tolkienian = word.copy()
        no_tolkienian["tolkienian_word"] = None
        self.assertFalse(are_tolkienian_duplicates(word, no_tolkienian))

        other_tolkienian = word.copy()
        other_tolkienian["tolkienian_word"] = "other"
        self.assertFalse(are_tolkienian_duplicates(word, other_tolkienian))

        other_english = word.copy()
        other_english["english_word"] = "other"
        self.assertTrue(are_tolkienian_duplicates(word, other_english))

        other_stem = word.copy()
        other_stem["stem"] = "other"
        self.assertFalse(are_tolkienian_duplicates(word, other_stem))

        other_extra = word.copy()
        other_extra["extra_info"] = "other"
        self.assertFalse(are_tolkienian_duplicates(word, other_extra))

        other_pos = word.copy()
        other_pos["part_of_speech"] = "other"
        self.assertTrue(are_tolkienian_duplicates(word, other_pos))

    def test_words_are_english_duplicates(self):
        word = {"tolkienian_word": "tolkienian", "english_word": "english", "stem": "stem", "extra_info": "extra", "part_of_speech": "n"}

        no_english = word.copy()
        no_english["english_word"] = None
        self.assertFalse(are_english_duplicates(word, no_english))

        other_tolkienian = word.copy()
        other_tolkienian["tolkienian_word"] = "other"
        self.assertTrue(are_english_duplicates(word, other_tolkienian))

        other_english = word.copy()
        other_english["english_word"] = "other"
        self.assertFalse(are_english_duplicates(word, other_english))

        other_stem = word.copy()
        other_stem["stem"] = "other"
        self.assertTrue(are_english_duplicates(word, other_stem))

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

    def test_merging_tolkienian_duplicates(self):
        words = [
            {"tolkienian_word": "sívë", "english_word": "knowing"},
            {"tolkienian_word": "sívë", "english_word": "peace"},
            {"tolkienian_word": "sívë", "english_word": "as"},
        ]
        merge_duplicates(words, "english_word")
        self.assertEqual(words[0]["english_word"], "(1) as; (2) knowing; (3) peace")
        self.assertIsNone(words[1]["english_word"])
        self.assertIsNone(words[2]["english_word"])

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
        self.assertEqual(words[0]["tolkienian_word"], "(1) (a)lá; (2) test")
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

    def test_formatting_simple_word(self):
        word = {"tolkienian_word": "hîr", "english_word": "lord"}
        formatted = format_word(word)
        self.assertEqual(formatted, "hîr|lord\n")
    
    def test_formatting_word_with_stem(self):
        word = {"tolkienian_word": "hîr", "english_word": "lord", "stem": "hîr"}
        formatted = format_word(word)
        self.assertEqual(formatted, "hîr (hîr)|lord\n")
    
    def test_formatting_word_with_extra_info(self):
        word = {"tolkienian_word": "hîr", "english_word": "lord", "extra_info": "extra"}
        formatted = format_word(word)
        self.assertEqual(formatted, "hîr (extra)|lord\n")
    
    def test_formatting_word_with_part_of_speech(self):
        word = {"tolkienian_word": "hîr", "english_word": "lord", "part_of_speech": "n"}
        formatted = format_word(word)
        self.assertEqual(formatted, "hîr|lord (n)\n")

    def test_formatting_word_with_all(self):
        word = {"tolkienian_word": "mísë", "english_word": "grey", "stem": "*mísi-", "extra_info": "extra", "part_of_speech": "adj"}
        formatted = format_word(word)
        self.assertEqual(formatted, "mísë (*mísi-) (extra)|grey (adj)\n")

    def test_generating_sindarin_does_not_throw(self):
        args = parse_args()
        args.language = 'sindarin'
        main(args)

if __name__ == '__main__':
    unittest.main()
