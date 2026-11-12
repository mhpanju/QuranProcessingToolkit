"""Conventional chapter labels; source attribution is in THIRD_PARTY_NOTICES.md.

Arabic/English labels and verse counts: Tanzil metadata v1.0, (C) 2008-2009
Tanzil.info, upstream license identifier cc-by (version unspecified).
ASCII transliterations are this project's conventional labels.
Source: https://tanzil.net/res/text/metadata/quran-data.xml
Source SHA-256: 8867c1d88191472adec9db694b3cd9f135b1a2ef580574d32cf888dcb22c5c7a
"""

from __future__ import annotations

# (ASCII transliteration, Arabic name, English meaning, verse count)
CHAPTERS: tuple[tuple[str, str, str, int], ...] = (
    ("al-Fatihah", "الفاتحة", "The Opening", 7),
    ("al-Baqarah", "البقرة", "The Cow", 286),
    ("Al Imran", "آل عمران", "The Family of Imraan", 200),
    ("an-Nisa", "النساء", "The Women", 176),
    ("al-Maidah", "المائدة", "The Table", 120),
    ("al-Anam", "الأنعام", "The Cattle", 165),
    ("al-Araf", "الأعراف", "The Heights", 206),
    ("al-Anfal", "الأنفال", "The Spoils of War", 75),
    ("at-Tawbah", "التوبة", "The Repentance", 129),
    ("Yunus", "يونس", "Jonas", 109),
    ("Hud", "هود", "Hud", 123),
    ("Yusuf", "يوسف", "Joseph", 111),
    ("ar-Rad", "الرعد", "The Thunder", 43),
    ("Ibrahim", "ابراهيم", "Abraham", 52),
    ("al-Hijr", "الحجر", "The Rock", 99),
    ("an-Nahl", "النحل", "The Bee", 128),
    ("al-Isra", "الإسراء", "The Night Journey", 111),
    ("al-Kahf", "الكهف", "The Cave", 110),
    ("Maryam", "مريم", "Mary", 98),
    ("Ta-Ha", "طه", "Taa-Haa", 135),
    ("al-Anbiya", "الأنبياء", "The Prophets", 112),
    ("al-Hajj", "الحج", "The Pilgrimage", 78),
    ("al-Muminun", "المؤمنون", "The Believers", 118),
    ("an-Nur", "النور", "The Light", 64),
    ("al-Furqan", "الفرقان", "The Criterion", 77),
    ("ash-Shuara", "الشعراء", "The Poets", 227),
    ("an-Naml", "النمل", "The Ant", 93),
    ("al-Qasas", "القصص", "The Stories", 88),
    ("al-Ankabut", "العنكبوت", "The Spider", 69),
    ("ar-Rum", "الروم", "The Romans", 60),
    ("Luqman", "لقمان", "Luqman", 34),
    ("as-Sajdah", "السجدة", "The Prostration", 30),
    ("al-Ahzab", "الأحزاب", "The Clans", 73),
    ("Saba", "سبإ", "Sheba", 54),
    ("Fatir", "فاطر", "The Originator", 45),
    ("Ya-Sin", "يس", "Yaseen", 83),
    ("as-Saffat", "الصافات", "Those drawn up in Ranks", 182),
    ("Sad", "ص", "The letter Saad", 88),
    ("az-Zumar", "الزمر", "The Groups", 75),
    ("Ghafir", "غافر", "The Forgiver", 85),
    ("Fussilat", "فصلت", "Explained in detail", 54),
    ("ash-Shura", "الشورى", "Consultation", 53),
    ("az-Zukhruf", "الزخرف", "Ornaments of gold", 89),
    ("ad-Dukhan", "الدخان", "The Smoke", 59),
    ("al-Jathiyah", "الجاثية", "Crouching", 37),
    ("al-Ahqaf", "الأحقاف", "The Dunes", 35),
    ("Muhammad", "محمد", "Muhammad", 38),
    ("al-Fath", "الفتح", "The Victory", 29),
    ("al-Hujurat", "الحجرات", "The Inner Apartments", 18),
    ("Qaf", "ق", "The letter Qaaf", 45),
    ("adh-Dhariyat", "الذاريات", "The Winnowing Winds", 60),
    ("at-Tur", "الطور", "The Mount", 49),
    ("an-Najm", "النجم", "The Star", 62),
    ("al-Qamar", "القمر", "The Moon", 55),
    ("ar-Rahman", "الرحمن", "The Beneficent", 78),
    ("al-Waqiah", "الواقعة", "The Inevitable", 96),
    ("al-Hadid", "الحديد", "The Iron", 29),
    ("al-Mujadilah", "المجادلة", "The Pleading Woman", 22),
    ("al-Hashr", "الحشر", "The Exile", 24),
    ("al-Mumtahanah", "الممتحنة", "She that is to be examined", 13),
    ("as-Saff", "الصف", "The Ranks", 14),
    ("al-Jumuah", "الجمعة", "Friday", 11),
    ("al-Munafiqun", "المنافقون", "The Hypocrites", 11),
    ("at-Taghabun", "التغابن", "Mutual Disillusion", 18),
    ("at-Talaq", "الطلاق", "Divorce", 12),
    ("at-Tahrim", "التحريم", "The Prohibition", 12),
    ("al-Mulk", "الملك", "The Sovereignty", 30),
    ("al-Qalam", "القلم", "The Pen", 52),
    ("al-Haqqah", "الحاقة", "The Reality", 52),
    ("al-Maarij", "المعارج", "The Ascending Stairways", 44),
    ("Nuh", "نوح", "Noah", 28),
    ("al-Jinn", "الجن", "The Jinn", 28),
    ("al-Muzzammil", "المزمل", "The Enshrouded One", 20),
    ("al-Muddaththir", "المدثر", "The Cloaked One", 56),
    ("al-Qiyamah", "القيامة", "The Resurrection", 40),
    ("al-Insan", "الانسان", "Man", 31),
    ("al-Mursalat", "المرسلات", "The Emissaries", 50),
    ("an-Naba", "النبإ", "The Announcement", 40),
    ("an-Naziat", "النازعات", "Those who drag forth", 46),
    ("Abasa", "عبس", "He frowned", 42),
    ("at-Takwir", "التكوير", "The Overthrowing", 29),
    ("al-Infitar", "الإنفطار", "The Cleaving", 19),
    ("al-Mutaffifin", "المطففين", "Defrauding", 36),
    ("al-Inshiqaq", "الإنشقاق", "The Splitting Open", 25),
    ("al-Buruj", "البروج", "The Constellations", 22),
    ("at-Tariq", "الطارق", "The Morning Star", 17),
    ("al-Ala", "الأعلى", "The Most High", 19),
    ("al-Ghashiyah", "الغاشية", "The Overwhelming", 26),
    ("al-Fajr", "الفجر", "The Dawn", 30),
    ("al-Balad", "البلد", "The City", 20),
    ("ash-Shams", "الشمس", "The Sun", 15),
    ("al-Layl", "الليل", "The Night", 21),
    ("ad-Duha", "الضحى", "The Morning Hours", 11),
    ("ash-Sharh", "الشرح", "The Consolation", 8),
    ("at-Tin", "التين", "The Fig", 8),
    ("al-Alaq", "العلق", "The Clot", 19),
    ("al-Qadr", "القدر", "The Power, Fate", 5),
    ("al-Bayyinah", "البينة", "The Evidence", 8),
    ("az-Zalzalah", "الزلزلة", "The Earthquake", 8),
    ("al-Adiyat", "العاديات", "The Chargers", 11),
    ("al-Qariah", "القارعة", "The Calamity", 11),
    ("at-Takathur", "التكاثر", "Competition", 8),
    ("al-Asr", "العصر", "The Declining Day, Epoch", 3),
    ("al-Humazah", "الهمزة", "The Traducer", 9),
    ("al-Fil", "الفيل", "The Elephant", 5),
    ("Quraysh", "قريش", "Quraysh", 4),
    ("al-Maun", "الماعون", "Almsgiving", 7),
    ("al-Kawthar", "الكوثر", "Abundance", 3),
    ("al-Kafirun", "الكافرون", "The Disbelievers", 6),
    ("an-Nasr", "النصر", "Divine Support", 3),
    ("al-Masad", "المسد", "The Palm Fibre", 5),
    ("al-Ikhlas", "الإخلاص", "Sincerity", 4),
    ("al-Falaq", "الفلق", "The Dawn", 5),
    ("an-Nas", "الناس", "Mankind", 6),
)


def chapter_name(number: int, representation: str = "transliteration") -> str:
    """Return a chapter name in transliteration, Arabic, or English."""
    if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= 114:
        raise ValueError("chapter number must be an integer from 1 through 114")
    aliases = {"transliteration": 0, "ascii": 0, "arabic": 1, "english": 2, "translation": 2}
    try:
        index = aliases[representation.lower()]
    except KeyError as error:
        raise ValueError(
            "name representation must be transliteration, arabic, or english"
        ) from error
    return str(CHAPTERS[number - 1][index])
