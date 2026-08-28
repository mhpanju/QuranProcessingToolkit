"""Load a user-supplied chapter|verse|translation file."""

import argparse

from quran_processing_toolkit import load_quran

parser = argparse.ArgumentParser()
parser.add_argument("translation_file")
arguments = parser.parse_args()

quran = load_quran(translation=arguments.translation_file)
quran.verses.show("english", limit=10)
