import argparse
import unittest
from generate import parse_args, main

class TestGenerate(unittest.TestCase):
    def test_generating_sindarin_does_not_throw(self):
        args = parse_args()
        args.language = 'sindarin'
        main(args)

if __name__ == '__main__':
    unittest.main()
