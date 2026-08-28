"""Print the number of verses in each of the Quran's 30 juz."""

from quran_processing_toolkit import load_quran


def main() -> None:
    corpus = load_quran()
    for juz in corpus.juzs:
        print(f"{juz.number}\t{juz.start.chapter}\t{juz.start.verse}\t{len(juz)}")


if __name__ == "__main__":
    main()
