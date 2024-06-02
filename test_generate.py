import unittest
from generate import add_uniqueness_via_field, format_word, parse_args, main

class TestGenerate(unittest.TestCase):
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
        word = {"tolkienian_word": "hîr", "english_word": "lord", "stem": "hîr", "extra_info": "extra", "part_of_speech": "n"}
        formatted = format_word(word)
        self.assertEqual(formatted, "hîr (hîr) (extra)|lord (n)\n")

    def test_generating_sindarin_does_not_throw(self):
        args = parse_args()
        args.language = 'sindarin'
        main(args)

if __name__ == '__main__':
    unittest.main()
