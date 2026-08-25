# 786/110
import json
from tqdm import tqdm


def loc_str_to_coords(loc_string: str):
    """
    Converts a string location identifier to a tuple of ints.

    :param loc_string: location of a token in the corpus of the form
                        "(chapter_num:verse_num:word_num:token_num)"
    :return: the four-entry tuple of ints
                        (chapter_num, verse_num, word_num, token_num)
    """
    # strip off the parentheses
    loc_string = loc_string.strip("()")
    return [int(_coordinate) for _coordinate in loc_string.split(":")]


def setup_data_for_verses_from_file(qc_object, filename: str, field_name: str, delimiter: str="|"):
    # Give Arabic text for each verse object
    with open(filename) as f:
        lines = f.readlines()
    for line in lines:
        if not line.strip():
            break
        ch_num, v_num, verse_str = line.strip().split(delimiter)
        ch_num, v_num = int(ch_num), int(v_num)

        # don't want to count basmala in first verse
        if ch_num > 1 and v_num == 1:
            verse_str = verse_str.replace("بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ ", "")
            verse_str = verse_str.replace("بِّسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ ", "")
        qc_object.chapters[ch_num-1].verses[v_num-1].set_field(field_name, verse_str)








class Token:
    # __slots__ = ()  # or define allowed fields explicitly

    def __init__(self, input_token_data):
        self.CHAPTER = None
        self.VERSE = None
        self.WORD = None
        self.WORD_PART = None
        self.FORM = None
        self.POS = None
        self.ROOT = None
        self.TOKEN_ROLE = None

        for token_k, token_v in input_token_data.items():
            object.__setattr__(self, token_k, token_v)


class Word:
    def __init__(self, chapter, verse, word):
        self.chapter = chapter
        self.verse = verse
        self.word = word
        self.address = (chapter, verse, word)
        self.tokens = []
        self.stem_tokens = [] # usually just one stem but sometimes two, like in "'amma"
        self.stem_part_of_speech = None
        self.root = None
        self.is_multi_stem = False

    def set_field(self, field_name: str, field_value):
        if field_name == "arabic_text":
            self.arabic_text = field_value

    def add_stem(self, stem_token: Token) -> None:
        self.stem_tokens.append(stem_token)
        if not self.stem_part_of_speech:
            self.stem_part_of_speech = stem_token.POS
            self.root = stem_token.ROOT
        else:
            self.stem_part_of_speech = [self.stem_part_of_speech, stem_token.POS]
            self.root = None # todo fix
            self.is_multi_stem = True

    def is_verb(self):
        return self.stem_part_of_speech == "V"

    def get_baab(self) -> str:
        if self.is_multi_stem:
            return None
        stem_token = self.stem_tokens[0]
        verb_form = getattr(stem_token, "VERB_FORM", None)
        if verb_form:
            return baab_number_to_name[verb_form]
        return None



class Verse:
    def __init__(self, chapter, verse):
        self.chapter = chapter
        self.verse = verse
        self.words = []
        self.arabic_text = None
        self.translation_text = None

    def set_field(self, field_name: str, field_value):
        if field_name == "arabic_text":
            self.arabic_text = field_value
        elif field_name == "translation_text":
            self.translation_text = field_value


class Chapter:
    def __init__(self, chapter):
        self.chapter = chapter
        self.verses = []


class QuranCorpus:

    def __init__(self):
        with open("corpus/quran-morphologies.json") as f:
            full_data = json.load(f)

        self.chapters = []
        self.verses = []
        self.words = []
        self.tokens = []
        current_ch = None
        current_v = None
        current_w = None

        for d in tqdm(full_data, desc="Loading Qur'an morphological data...", unit="token"):
            ch, v, w, wp = d["CHAPTER"], d["VERSE"], d["WORD"], d["WORD_PART"]

            # New chapter?
            if current_ch is None or ch != current_ch.chapter:
                current_ch = Chapter(ch)
                self.chapters.append(current_ch)
                current_v = None
                current_w = None

            # New verse?
            if current_v is None or v != current_v.verse:
                current_v = Verse(ch, v)
                current_ch.verses.append(current_v)
                self.verses.append(current_v)
                current_w = None

            # New word?
            if current_w is None or w != current_w.word:
                current_w = Word(ch, v, w)
                current_v.words.append(current_w)
                self.words.append(current_w)

            # Always add token
            current_t = Token(d)
            current_w.tokens.append(current_t)
            if current_t.TOKEN_ROLE == "STEM":
                current_w.add_stem(current_t)
            self.tokens.append(current_t)

        setup_data_for_verses_from_file(self, "corpus/uthmani-numbered.txt", "arabic_text")
        setup_data_for_verses_from_file(self, "corpus/translation_qarai.txt", "translation_text")

        remove_chars = ['ۛ', 'ۖ', 'ۗ', 'ۚ', 'ۙ', 'ۘ', '۩', 'ۜ', 'ۜ', ]
        for verse in self.verses:
            arabic_words = verse.arabic_text
            arabic_words = arabic_words.replace("بَعْدَ مَا", "بَعْد###مَا")
            arabic_words = arabic_words.replace("إِلْ يَاسِينَ", "إِلْ###يَاسِينَ" )
            for remove_char in remove_chars:
                arabic_words = arabic_words.replace(remove_char, "")
            arabic_words = arabic_words.strip().split()
            if len(arabic_words) == len(verse.words):
                for arabic_word, word_obj in zip(arabic_words, verse.words):
                    word_obj.set_field("arabic_text", arabic_word.replace("###", " "))
            else:
                print("Oops, word counts don't align")


    # want to be able to do:

    # see transliteration for each word, verse

    # find all verses with a verb having "k" in root
    # for verse in qc.verses:
    #   for word in verse.words:
    #       if word.is_verb() and "k" in word.root:
    #          thingy




slabel_to_seegha = {
    "3MS": 1,
    "3MD": 2,
    "3MP": 3,
    "3FS": 4,
    "3FD": 5,
    "3FP": 6,
    "2MS": 7,
    "2MD": 8,
    "2MP": 9,
    "2FS": 10,
    "2FD": 11,
    "2FP": 12,
    "1S": 13,
    "1P": 14,
    "2D": 0
}

clabel_to_case = {
    "GEN": "GEN",
    "NOM": "NOM",
    "ACC": "ACC"
}

baab_number_to_name = {
    "I": "Thulathy Mujarrad",
    "II": "Taf'eel",
    "III": "Mufaa'alah",
    "IV": "If'aal",
    "V": "Tafa'ul",
    "VI": "Tafaa'ul",
    "VII": "Infi'aal",
    "VIII": "Ifti'aal",
    "IX": "If'ilaal",
    "X": "Istif'aal",
    "XI": "If'eelaal",
    "XII": "Other",
    "rI": "Ruba'iy Mujarrad",
    "rII": "",
    "rIII": "",
    "rIV": "If'illaal",
}


if __name__ == "__main__":
    print("Bismillah")
    qc = QuranCorpus()


    # Find which baab each root appears in
    roots_to_baabs = dict()
    for word in qc.words:
        baab = word.get_baab()
        if baab:
            # if not word.is_verb():
            #     continue
            root = word.root
            arabic_text = word.arabic_text
            if root not in roots_to_baabs:
                roots_to_baabs[root] = dict()
            if baab not in roots_to_baabs[root]:
                roots_to_baabs[root][baab] = {}
            if word.arabic_text not in roots_to_baabs[root][baab]:
                roots_to_baabs[root][baab][arabic_text] = []
            roots_to_baabs[root][baab][arabic_text].append(word.address)
    sorted_by_num_baabs = sorted([(k, len(v),
                                   sorted([(baab_name,
                                            sorted([(w_k, w_v_list) for w_k, w_v_list in w_dict.items()],
                                                   key=lambda z: len(z[1]), reverse=True))
                                           for baab_name, w_dict in v.items()],
                                          key=lambda y: len(y[1]), reverse=True))
                                  for k, v in roots_to_baabs.items()],
                                 key=lambda x: x[1], reverse=True)

    for k, n, v_list in sorted_by_num_baabs:
        print(f"{k}\t{n}\t{v_list}")

    # find all verses with a verb having "k" in root
    seen_roots = []
    for verse in qc.verses:
      for word in verse.words:
          if word.is_verb() and "k" in word.root and word.root not in seen_roots:
              print(word.root)
              seen_roots.append(word.root)

    # cases
    """
    for d in qc.full_data:
        found_case = False
        for feat in d["features"]:
            if feat.startswith("("):
                d["VERB_FORM"] = feat[1:-1]
                found_case = True
                d["features"].remove(feat)
                break
        if not found_case and d.get("POS") == "V":
            d["VERB_FORM"] = "I"
            found_case = True
        if found_case and len(d["ROOT"]) == 4:
            d["VERB_FORM"] = "r" + d["VERB_FORM"]
    """

    # seeghas
    """
    for d in qc.full_data:
        found_case = False
        for feat in d["features"]:
            if feat in slabel_to_seegha:
                if d.get("PRON", feat) != feat:
                    print()
                d["CONJUGATE"] = slabel_to_seegha[feat]
                d["features"].remove(feat)
                break
    """



    # cases
    """
    for d in qc.full_data:
        for feat in d["features"]:
            if feat in clabel_to_case:
                d["CASE"] = clabel_to_case[feat]
                d["features"].remove(feat)
                break

        if d.get("MOOD") == "SUBJ":
            d["CASE"] = "ACC"
        elif d.get("MOOD", "") == "JUS":
            d["CASE"] = "JUS"
        elif "IMPF" in d["features"]:
            d["CASE"] = "NOM"
        elif "IMPV" in d["features"]:
            d["CASE"] = "MABNI"
    


    # stem/pre/suffix
    fix_types = {"PREFIX": "PREFIX",
                 "SUFFIX": "SUFFIX",
                 "STEM": "STEM",
                 "sSTEM": "STEM"}
    definiteness = {"DEF"}
    for d in qc.full_data:
        for feat in d["features"]:
            if feat in fix_types:
                d["TOKEN_ROLE"] = fix_types[feat]
                d["features"].remove(feat)



    x = [   (2,35,7,2),
            (2,35,11,1),
            (2,35,13,1),
            (2,35,16,2),
            (3,122,6,1),
            (4,171,4,1),
            (5,77,5,1),
            (7,19,9,1),
            (7,19,11,1),
            (7,19,14,2),
            (7,20,20,1),
            (7,20,23,1),
            (7,21,3,2),
            (7,22,23,2),
            (7,22,26,2),
            (10,78,9,2),
            (10,78,15,2),
            (10,89,7,1),
            (12,37,12,1),
            (12,41,19,1),
            (20,42,6,1),
            (20,44,1,2),
            (20,46,3,1),
            (20,47,2,2)]




    # fix seegha 0 to become 8
    for d in qc.full_data:
        # for item in x:
        #     if (d['CHAPTER'],d['VERSE'],d['WORD'],d['WORD_PART']) == item:
        #         d["CONJUGATE"] = 0

        # if d["CHAPTER"] == 28 and d["VERSE"] == 23 and d["WORD"] == 15 and d["WORD_PART"] == 1:
        #     d["CONJUGATE"] = 0

        if d.get("CONJUGATE") == 0:
            d["CONJUGATE"] = 8

            print(d)

    tenses = {"IMPF": "PAST",
              "PERF": "PRES",
              "IMPV": "IMPV"}
    # tense
    # for d in qc.full_data:
    #     found_tense = False
    #     for feat in d["features"]:
    #         if feat in tenses:
    #             d["TENSE"] = tenses[feat]
    #             d["features"].remove(feat)
    #             found_tense = True
    #     if d.get("POS") == "V" and not found_tense:
    #         print(d)


    voices = {"ACT": "ACTIVE",
              "PASS": "PASSIVE",
              }
    # voice
    for d in qc.full_data:
        found_voice = False
        for feat in d["features"]:
            if feat in voices:
                d["VOICE"] = voices[feat]
                d["features"].remove(feat)
                found_voice = True
        if d.get("POS") == "V" and not found_voice:
            d["VOICE"] = "ACTIVE"

    genders = {"M": "MASC",
               "MP": "MASC",
               "MS": "MASC",
               "MD": "MASC",
               "F": "FEM",
               "FP": "FEM",
               "FS": "FEM",
               "FD": "FEM",
              }
    counts = {
        "MP": "PLURAL",
        "MD": "DUAL",
        "MS": "SINGULAR",
        "FP": "PLURAL",
        "FD": "DUAL",
        "FS": "SINGULAR"
    }

    # gender
    poses = {}
    for d in qc.full_data:
        found_gender = False
        for feat in d["features"]:
            if feat in genders:
                d["GENDER"] = genders[feat]
                found_gender = True
                if feat in counts:
                    d["COUNT"] = counts[feat]
                d["features"].remove(feat)

                if d["POS"] not in poses:
                    poses[d["POS"]] = []
                poses[d["POS"]].append(d)

            elif feat in counts:
                d["COUNT"] = counts[feat]
                d["features"].remove(feat)



    """

    indef_endings = ["K", "pF", "'F", "FA", "FY", "N", "F[A", "&NA@", "pF[", "'F[", "K]", "N["]
    indef_count = 0
    for d in qc.full_data:
        if "INDEF" in d["features"]:
            if not any([d["FORM"].endswith(ending) for ending in indef_endings]):
                print(d)
                print()
                indef_count += 1

    print(indef_count)
    print()

    feature_kinds = set()
    for d in qc.full_data:
        feature_kinds.update(d["features"])

    for feature in feature_kinds:
        print(feature)


    print()
    print("Starting")

    set_of_fields = {}

    for d in qc.full_data:
        # if "PCPL" in d["features"]:
        #     if not "VOICE" in d:
        #         print("Uhoh:")
        #         print(d)
        #     else:
        #         voice = d["VOICE"]
        #         if voice == "ACTIVE":
        #             d["DERIVED_NOUN"] = "VERB_SUBJECT"
        #         elif voice == "PASSIVE":
        #             d["DERIVED_NOUN"] = "VERB_OBJECT"
        #         else:
        #             print("uhoh")
        #             print(d)
        #         d.pop("VOICE")
        #         d["features"].remove("PCPL")




        # if "VN" in d["features"]:
        #     if "VOICE" in d:
        #         print("Uhoh:")
        #         print(d)
        #     else:
        #         d["DERIVED_NOUN"] = "VERB_OBJECT"
        #         d["features"].remove("VN")



        # is it the case that every token with + feature has token_role=prefix?
        # for f in d["features"]:
        #     if "+" in f:
        #         d["features"].remove(f)

        # for
        # if any([("+" in f) for f in d["features"]]):
        #     if d.get("TOKEN_ROLE", "") != "PREFIX":
        #         print(d)
        # if "P" in d["features"]:
        #     print(d["FORM"])
        #     if d.get("COUNT"):
        #         print(d)
        #     d["COUNT"] = "PLURAL"
        #     d["UNUSUAL_PLURAL_ORIGINALLY_P_FEATURE"] = True
        #     d["features"].remove("P")

        for k, v in d.items():
            if k == "features":
                if v:
                    print("uhoh")
                    print(v)
                continue
            if k not in set_of_fields:
                set_of_fields[k] = {v}
            else:
                set_of_fields[k] |= {v}

        d.pop("features")
    print("done")

    for field, values in set_of_fields.items():
        print(f"{field}: {list(values)[:10]}")

    # Fix l: types
    # is every noun without "INDEFINITE" definiteness, definite?


    # with open("QM_temp9.json", "w") as f:
    #     json.dump(qc.full_data, f, indent=True)
