# 786/110
import json


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









class Token:

    def __init__(self):
        return


class Word:

    def __init__(self):
        return

    def get_stem(self) -> Token:
        return Token()


class Verse:

    def __init__(self):
        return


class Chapter:

    def __init__(self):
        return


class QuranCorpus:

    def __init__(self):
        with open("QM_temp3.json") as f:
            self.full_data = json.load(f)

        # Set up list of chapters and verses
        self.chapters = []
        self.verses = []
        # for loc_str, entry in self.full_data.items():
        #     chapter_num, verse_num, word_num, token_num = loc_str_to_coords(loc_str)




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
    print(len(qc.full_data))
    print(loc_str_to_coords("(1:2:4:3)"))


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






    feature_kinds = set()
    for d in qc.full_data:
        feature_kinds.update(d["features"])

    for feature in feature_kinds:
        print(feature)

    with open("QM_temp3.json", "w") as f:
        json.dump(qc.full_data, f, indent=True)
