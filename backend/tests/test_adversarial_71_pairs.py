import pytest
from scraper.tmdb_top_ingestor import evaluate_candidate_match


# 41 ta asl adversarial juftliklar
ADVERSARIAL_41_PAIRS = [
    # 1-10
    (('The Godfather Part II', 'Крестный отец 2', 'The Godfather Part II', 1974), ('Choqintirgan ota 2', 1974), True, 'Sequel Part II match'),
    (('The Godfather', 'Крестный отец', 'The Godfather', 1972), ('Choqintirgan ota 2', 1974), False, 'Sequel 2 vs original 1'),
    (('The Godfather Part II', 'Крестный отец 2', 'The Godfather Part II', 1974), ('Choqintirgan ota', 1972), False, 'Original 1 vs sequel 2'),
    (('Dune', 'Дюна', 'Dune', 2021), ('Dyuna', 1984), False, 'Remake different year'),
    (('Dune: Part Two', 'Дюна 2', 'Dune: Part Two', 2024), ('Dyuna 2', 2024), True, 'Part Two match'),
    (('Dune', 'Дюна', 'Dune', 2021), ('Dyuna 2', 2024), False, 'Part 1 vs Part 2'),
    (('Spider-Man 2', 'Человек-паук 2', 'Spider-Man 2', 2004), ('Orgimchak odam 2', 2004), True, 'Spider-Man 2 match'),
    (('Spider-Man', 'Человек-паук', 'Spider-Man', 2002), ('Orgimchak odam 3', 2007), False, 'Part 1 vs Part 3'),
    (('Avatar', 'Аватар', 'Avatar', 2009), ('Avatar: Suv yoli', 2022), False, 'Avatar 1 vs Avatar 2'),
    (('Avatar: The Way of Water', 'Аватар: Путь воды', 'Avatar: The Way of Water', 2022), ('Avatar: Suv yoli / Avatar: The Way of Water', 2022), True, 'Avatar 2 match'),

    # 11-20
    (('Drive', 'Драйв', 'Drive', 2011), ('Gazabli drayv / Drive Angry', 2011), False, 'SF-001 Drive vs Drive Angry'),
    (('Drive', 'Драйв', 'Drive', 2011), ('Drayv / Drive', 2011), True, 'Drive match'),
    (('Iron Man', 'Железный человек', 'Iron Man', 2008), ('Temir odam 2', 2010), False, 'Iron Man 1 vs Iron Man 2'),
    (('Iron Man 3', 'Железный человек 3', 'Iron Man 3', 2013), ('Temir odam 3', 2013), True, 'Iron Man 3 match'),
    (('Gladiator', 'Гладиатор', 'Gladiator', 2000), ('Gladiator 2', 2024), False, 'Gladiator 1 vs Gladiator 2'),
    (('Joker', 'Джокер', 'Joker', 2019), ('Joker 2', 2024), False, 'Joker 1 vs Joker 2'),
    (('Deadpool', 'Дэдпул', 'Deadpool', 2016), ('Dedpul va Rosomaxa', 2024), False, 'Deadpool 1 vs Deadpool & Wolverine'),
    (('Shrek 2', 'Шрэк 2', 'Shrek 2', 2004), ('Shrek 2 Uzbek tilida', 2004), True, 'Shrek 2 match'),
    (('Shrek', 'Шрэк', 'Shrek', 2001), ('Shrek 4', 2010), False, 'Shrek 1 vs Shrek 4'),
    (('Toy Story 3', 'История игрушек 3', 'Toy Story 3', 2010), ('Oyinchoqlar tarixi 3', 2010), True, 'Toy Story 3 match'),

    # 21-30
    (('Toy Story', 'История игрушек', 'Toy Story', 1995), ('Oyinchoqlar tarixi 2', 1999), False, 'Toy Story 1 vs 2'),
    (('Interstellar', 'Интерстеллар', 'Interstellar', 2014), ('Interstellar Uzbek tilida', 2014), True, 'Interstellar exact'),
    (('Inception', 'Начало', 'Inception', 2010), ('Muqaddima / Inception', 2010), True, 'Inception bilingual'),
    (('Top Gun', 'Лучший стрелок', 'Top Gun', 1986), ('Top Gun: Maverik', 2022), False, 'Top Gun 1 vs Top Gun Maverick'),
    (('Top Gun: Maverick', 'Топ Ган: Мэверик', 'Top Gun: Maverick', 2022), ('Top Gun: Maverik', 2022), True, 'Top Gun Maverick match'),
    (('Fast & Furious', 'Форсаж 4', 'Fast & Furious', 2009), ('Forsaj 1', 2001), False, 'Fast 4 vs Fast 1'),
    (('Fast Five', 'Форсаж 5', 'Fast Five', 2011), ('Forsaj 5', 2011), True, 'Fast 5 match'),
    (('Mission: Impossible', 'Миссия невыполнима', 'Mission: Impossible', 1996), ('Uddalab bolmas topshiriq 2', 2000), False, 'MI 1 vs MI 2'),
    (('Kung Fu Panda 2', 'Кунг-фу Панда 2', 'Kung Fu Panda 2', 2011), ('Kung-fu panda 2', 2011), True, 'Kung Fu Panda 2 match'),
    (('Kung Fu Panda', 'Кунг-фу Панда', 'Kung Fu Panda', 2008), ('Kung-fu panda 3', 2016), False, 'Panda 1 vs Panda 3'),

    # 31-41
    (('Cars', 'Тачки', 'Cars', 2006), ('Tachki 2', 2011), False, 'Cars 1 vs Cars 2'),
    (('Cars 2', 'Тачки 2', 'Cars 2', 2011), ('Tachki 2', 2011), True, 'Cars 2 match'),
    (('Finding Nemo', 'В поисках Немо', 'Finding Nemo', 2003), ('V poiskax Dori', 2016), False, 'Nemo vs Dory'),
    (('Frozen', 'Холодное сердце', 'Frozen', 2013), ('Muz yurak 2', 2019), False, 'Frozen 1 vs Frozen 2'),
    (('Frozen II', 'Холодное сердце 2', 'Frozen II', 2019), ('Muz yurak 2', 2019), True, 'Frozen II match'),
    (('The Matrix', 'Матрица', 'The Matrix', 1999), ('Matrica: Qayta yuklash', 2003), False, 'Matrix 1 vs Reloaded'),
    (('The Matrix', 'Матрица', 'The Matrix', 1999), ('Matritsa / Matrix', 1999), True, 'Matrix 1 match'),
    (('Alien', 'Чужой', 'Alien', 1979), ('Begona: Romul', 2024), False, 'Alien 1 vs Alien Romulus'),
    (('Batman Begins', 'Бэтмен: Начало', 'Batman Begins', 2005), ('Qora ritsari', 2008), False, 'Batman Begins vs Dark Knight'),
    (('Halloween', 'Хэллоуин', 'Halloween', 1978), ('Xellouin', 2018), False, 'Remake Halloween 1978 vs 2018'),
    (('Spirited Away', 'Унесенные призраками', 'Sen to Chihiro no Kamikakushi', 2001), ('Arvohlar olamiga sayohat / Spirited Away', 2001), True, 'Spirited away match')
]

# 30 ta yangi adversarial juftliklar: anime fasllari, Kirill/Lotin transliteratsiyasi, remeyklar
NEW_30_PAIRS = [
    # Anime seasons (1-10)
    (('Attack on Titan', 'Атака титанов', 'Shingeki no Kyojin', 2013), ('Titanlar hujumi 2-fasl / Shingeki no Kyojin Season 2', 2017), False, 'Anime Titan S1 vs S2'),
    (('Attack on Titan Season 2', 'Атака титанов 2', 'Shingeki no Kyojin Season 2', 2017), ('Shingeki no Kyojin Season 2', 2017), True, 'Anime Titan S2 match'),
    (('Demon Slayer', 'Клинок рассекающий демонов', 'Kimetsu no Yaiba', 2019), ('Kimetsu no Yaiba: Mugen Ressha-hen', 2020), False, 'Anime Demon Slayer S1 vs Movie'),
    (('Demon Slayer: Kimetsu no Yaiba - The Movie: Mugen Train', 'Клинок рассекающий демонов: Поезд Бесконечный', 'Kimetsu no Yaiba: Mugen Ressha-hen', 2020), ('Kimetsu no Yaiba: Mugen Ressha-hen', 2020), True, 'Anime Demon Slayer Movie match'),
    (('Jujutsu Kaisen', 'Магическая битва', 'Jujutsu Kaisen', 2020), ('Sehrli jang 2-fasl / Jujutsu Kaisen Season 2', 2023), False, 'Anime Jujutsu S1 vs S2'),
    (('Jujutsu Kaisen Season 2', 'Магическая битва 2', 'Jujutsu Kaisen Season 2', 2023), ('Jujutsu Kaisen 2', 2023), True, 'Anime Jujutsu S2 match'),
    (('Naruto', 'Наруто', 'Naruto', 2002), ('Naruto: Shippuuden', 2007), False, 'Anime Naruto vs Naruto Shippuden'),
    (('Vinland Saga', 'Сага о Винланде', 'Vinland Saga', 2019), ('Vinland Saga Season 2', 2023), False, 'Anime Vinland S1 vs S2'),
    (('Tokyo Ghoul', 'Токийский гуль', 'Tokyo Kushu', 2014), ('Tokyo Ghoul: re', 2018), False, 'Anime Tokyo Ghoul vs Tokyo Ghoul re'),
    (('One-Punch Man', 'Ванпанчмен', 'One Punch Man', 2015), ('One-Punch Man Season 2', 2019), False, 'Anime One Punch Man S1 vs S2'),

    # Cyrillic/Latin transliteration (11-20)
    (('Interstellar', 'Интерстеллар', 'Interstellar', 2014), ('Interstellar', 2014), True, 'Translit Interstellar match'),
    (('The Avengers', 'Мстители', 'The Avengers', 2012), ('Qasoskorlar 2 / Mstiteli: Era Altrona', 2015), False, 'Translit Avengers 1 vs 2'),
    (('Avengers: Age of Ultron', 'Мстители: Эра Альтрона', 'Avengers: Age of Ultron', 2015), ('Mstiteli: Era Altrona', 2015), True, 'Translit Avengers 2 match'),
    (('Harry Potter and the Philosopher\'s Stone', 'Гарри Поттер и философский камень', 'Harry Potter and the Philosopher\'s Stone', 2001), ('Garri Potter va maxfiy hujra', 2002), False, 'HP 1 vs HP 2'),
    (('Harry Potter and the Chamber of Secrets', 'Гарри Поттер и тайная комната', 'Harry Potter and the Chamber of Secrets', 2002), ('Garri Potter va maxfiy hujra / Harry Potter and the Chamber of Secrets', 2002), True, 'HP 2 match'),
    (('Dune', 'Дюна', 'Dune', 2021), ('Dyuna', 2021), True, 'Translit Dyuna 2021 match'),
    (('Fight Club', 'Бойцовский клуб', 'Fight Club', 1999), ('Boytsovskiy klub / Fight Club', 1999), True, 'Translit Fight Club match'),
    (('Pulp Fiction', 'Криминальное чтиво', 'Pulp Fiction', 1994), ('Kriminalnoe chtivo / Pulp Fiction', 1994), True, 'Translit Pulp Fiction match'),
    (('The Wolf of Wall Street', 'Волк с Уолл-стрит', 'The Wolf of Wall Street', 2013), ('Uoll-stritlik bori / The Wolf of Wall Street', 2013), True, 'Translit Wolf of Wall Street match'),
    (('Pirates of the Caribbean: The Curse of the Black Pearl', 'Пираты Карибского моря: Проклятие Черной жемчужины', 'Pirates of the Caribbean: The Curse of the Black Pearl', 2003), ('Karib dengizi qaroqchilari 2: Murdalar sandig`i', 2006), False, 'Pirates 1 vs 2'),

    # Remakes & Different Years (21-30)
    (('Oldboy', 'Олдбой', 'Oldeuboi', 2003), ('Oldboy', 2013), False, 'Remake Oldboy 2003 vs 2013'),
    (('Oldboy', 'Олдбой', 'Oldboy', 2013), ('Oldboy', 2013), True, 'Remake Oldboy 2013 match'),
    (('The Lion King', 'Король Лев', 'The Lion King', 1994), ('Qirol sher / The Lion King', 2019), False, 'Remake Lion King 1994 vs 2019'),
    (('The Lion King', 'Король Лев', 'The Lion King', 2019), ('Qirol sher / The Lion King', 2019), True, 'Remake Lion King 2019 match'),
    (('Total Recall', 'Вспомнить всё', 'Total Recall', 1990), ('Eslab qol / Total Recall', 2012), False, 'Remake Total Recall 1990 vs 2012'),
    (('Beauty and the Beast', 'Красавица и чудовище', 'Beauty and the Beast', 1991), ('Sohibjamol va maxluq', 2017), False, 'Remake Beauty and Beast 1991 vs 2017'),
    (('Ghost in the Shell', 'Призрак в доспехах', 'Kokaku Kidotai', 1995), ('Prizrak v dospexax / Ghost in the Shell', 2017), False, 'Remake Ghost in the Shell 1995 vs 2017'),
    (('The Thing', 'Нечто', 'The Thing', 1982), ('Nechto', 2011), False, 'Remake The Thing 1982 vs 2011'),
    (('Suspiria', 'Суспирия', 'Suspiria', 1977), ('Suspiriya / Suspiria', 2018), False, 'Remake Suspiria 1977 vs 2018'),
    (('Ben-Hur', 'Бен-Гур', 'Ben-Hur', 1959), ('Ben-Gur / Ben-Hur', 2016), False, 'Remake Ben-Hur 1959 vs 2016')
]

ALL_71_PAIRS = ADVERSARIAL_41_PAIRS + NEW_30_PAIRS


def test_adversarial_41_pairs():
    """
    41 ta asl juftlikni sinovdan o'tkazish.
    Soxta ijobiy (False Positive) 0 bo'lishi shart.
    """
    tp = tn = fp = fn = 0
    fp_cases = []
    for (ten, tru, torig, yr), (scraped_t, scraped_yr), expected, desc in ADVERSARIAL_41_PAIRS:
        matched, reason = evaluate_candidate_match(
            seed_title_en=ten, seed_title_ru=tru, seed_orig_title=torig, seed_year=yr,
            scraped_title=scraped_t, scraped_year=scraped_yr
        )
        if expected and matched:
            tp += 1
        elif not expected and not matched:
            tn += 1
        elif not expected and matched:
            fp += 1
            fp_cases.append(f"FP in '{desc}': {ten} matched {scraped_t} ({reason})")
        elif expected and not matched:
            fn += 1

    assert fp == 0, f"False Positive topildi ({len(fp_cases)} ta):\n" + "\n".join(fp_cases)
    # Tasdiq: 41 juftlikda 0 ta FP!
    print(f"\n[41 PAIRS] TP={tp}, TN={tn}, FP={fp}, FN={fn}")


def test_adversarial_71_pairs():
    """
    Barcha 71 ta adversarial juftlikni (41 asl + 30 yangi) sinovdan o'tkazish.
    Anime fasllari, Kirill/Lotin transliteratsiyasi va remeyklarda 0 ta FP bo'lishi shart.
    """
    tp = tn = fp = fn = 0
    fp_cases = []
    for (ten, tru, torig, yr), (scraped_t, scraped_yr), expected, desc in ALL_71_PAIRS:
        matched, reason = evaluate_candidate_match(
            seed_title_en=ten, seed_title_ru=tru, seed_orig_title=torig, seed_year=yr,
            scraped_title=scraped_t, scraped_year=scraped_yr
        )
        if expected and matched:
            tp += 1
        elif not expected and not matched:
            tn += 1
        elif not expected and matched:
            fp += 1
            fp_cases.append(f"FP in '{desc}': {ten} matched {scraped_t} ({reason})")
        elif expected and not matched:
            fn += 1

    assert fp == 0, f"False Positive topildi ({len(fp_cases)} ta):\n" + "\n".join(fp_cases)
    print(f"\n[71 PAIRS] Total=71, TP={tp}, TN={tn}, FP={fp}, FN={fn}")
