import unittest
from generate import format_word, parse_args, main

class TestGenerate(unittest.TestCase):
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
