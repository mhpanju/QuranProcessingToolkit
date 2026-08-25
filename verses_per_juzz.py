from tools import QuranCorpus
from csv import reader


juzz_data = []
with open("corpus/juzz-breakdown.tsv", "r") as f:
    lines = reader(f, delimiter="\t")
    for line in lines:
        juzz_data.append({
            "chapter": int(line[1]),
            "verse": int(line[2])
        })

# for convenience, not real!!
juzz_data.append({
    "chapter": 115,
    "verse": 1
})

qc = QuranCorpus()

current_juzz_start_chapter = 0
current_juzz_start_verse = 0
current_juzz_index = 0
num_verses = 0
for verse in qc.verses:
    if verse.chapter < current_juzz_start_chapter or verse.verse < current_juzz_start_verse:
        num_verses += 1
    else:
        juzz_data[current_juzz_index-1]["num_verses"] = num_verses
        current_juzz_index += 1
        current_juzz_start_chapter = juzz_data[current_juzz_index]["chapter"]
        current_juzz_start_verse = juzz_data[current_juzz_index]["verse"]
        num_verses = 1
juzz_data[current_juzz_index-1]["num_verses"] = num_verses

for i, juzz_datum in enumerate(juzz_data):


    print(f"{i+1}\t{juzz_datum['chapter']}\t{juzz_datum['verse']}\t{juzz_datum['num_verses']}")

