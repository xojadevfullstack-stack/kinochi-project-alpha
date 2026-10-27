export interface CatalogTheme {
  id: string;
  title: string;
  count: number | string;
  href: string;
  category: "theme" | "franchise" | "genre" | "country";
  description?: string;
  posters: string[];
}

export const CURATED_CATALOG_THEMES: CatalogTheme[] = [
  {
    id: "harry-potter",
    title: "Sehrgarlar va Garri Potter olami",
    count: "8 ta kino",
    href: "/collections/harry-potter",
    category: "franchise",
    description: "Xogvarts sehrgarlari, Nyut Skamander va sehrli afsungarlar olami.",
    posters: [
      "https://image.tmdb.org/t/p/w500/wuMc08IPKEatf9rnMNXvIDxqP4W.jpg",
      "https://image.tmdb.org/t/p/w500/fECBtHlr0RB3foNHDiCBXeg9Bv9.jpg",
      "https://image.tmdb.org/t/p/w500/h6NYfVUyM6CDURtZSnBpz647Ldd.jpg"
    ]
  },
  {
    id: "qashqirlar-makoni",
    title: "Qashqirlar makoni (Kurtlar Vadisi)",
    count: "5 ta film va serial",
    href: "/collections/qashqirlar-makoni",
    category: "franchise",
    description: "Polat Alemdar, mafiya olami, Iroq, Falastin va Vatan janglari xronologiyasi.",
    posters: [
      "https://media.themoviedb.org/t/p/w440_and_h660_face/zPv5KaNEVqZLpbH6sEAvld9nMVr.jpg",
      "https://m.media-amazon.com/images/M/MV5BZjE1MzlhY2ItY2FhYy00NjFjLTk1ZDMtOWNkZTU4YTk4N2E1XkEyXkFqcGc@._V1_QL75_UY562_CR11,0,380,562_.jpg",
      "https://image.tmdb.org/t/p/w500/wDWkjobSJm8I5r2ctSPtneUjHxT.jpg"
    ]
  },
  {
    id: "taxtlar-oyini",
    title: "Ajdarlar va Taxtlar olami (Vesteros)",
    count: "2 ta serial",
    href: "/collections/taxtlar-oyini",
    category: "franchise",
    description: "Temir Taxt uchun qonli kurash, Targarirlar sulolasi va Oq yuruvchilar.",
    posters: [
      "https://image.tmdb.org/t/p/w500/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
      "https://image.tmdb.org/t/p/original/7V0Ebks0GgpKvQ7QbLAIdX5dos4.jpg",
      "https://image.tmdb.org/t/p/w500/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg"
    ]
  },
  {
    id: "vampirlar-va-borilar",
    title: "Vampirlar va Bo'rilar olami",
    count: "3 ta serial",
    href: "/collections/vampirlar-va-borilar",
    category: "theme",
    description: "Mistik Folls, Mayklsonlar xonadoni va bo'rilar to'dasi to'qnashuvi.",
    posters: [
      "https://image.tmdb.org/t/p/w500/gbp4zM0FE0n23X4UFY5EBlacrog.jpg",
      "https://image.tmdb.org/t/p/w500/keJOhJXGiLL54EW6QocbyvQGquA.jpg",
      "https://image.tmdb.org/t/p/w500/wjKBTcNy1xihmExqJI8kM2qvavP.jpg"
    ]
  },
  {
    id: "christopher-nolan",
    title: "Kristofer Nolan ilmiy-fantastikasi",
    count: "2 ta kino",
    href: "/collections/christopher-nolan",
    category: "theme",
    description: "Inception va Interstellar — ong osti labirinti va galaktikalararo vaqt sayohati.",
    posters: [
      "https://image.tmdb.org/t/p/w500/yQvGrMoipbRoddT0ZR8tPoR7NfX.jpg",
      "https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg",
      "https://image.tmdb.org/t/p/w500/yQvGrMoipbRoddT0ZR8tPoR7NfX.jpg"
    ]
  },
  {
    id: "superheroes",
    title: "Superqahramonlar va Qasoskorlar",
    count: "2 ta loyiha",
    href: "/collections/superheroes",
    category: "theme",
    description: "Qasoskorlar 4 Intiho va Yigitlar (The Boys) — superqahramonlar to'qnashuvi.",
    posters: [
      "https://image.tmdb.org/t/p/w500/bR8ISy1O9XQxqiy0fQFw2BX72RQ.jpg",
      "https://image.tmdb.org/t/p/original/in1R2dDc421JxsoRWaIIAqVI2KE.jpg",
      "https://image.tmdb.org/t/p/w500/bR8ISy1O9XQxqiy0fQFw2BX72RQ.jpg"
    ]
  },
  {
    id: "gladiatorlar",
    title: "Gladiatorlar va Qadimgi Rim",
    count: "1 ta kino",
    href: "/collections/gladiatorlar",
    category: "theme",
    description: "Kolizey janglari, Rim imperatori xiyonati va Maksimusning shonli qasosi.",
    posters: [
      "https://image.tmdb.org/t/p/w500/aDb548BOkFfI4nFm0kx8A3Ezh7H.jpg",
      "https://image.tmdb.org/t/p/w500/aDb548BOkFfI4nFm0kx8A3Ezh7H.jpg",
      "https://image.tmdb.org/t/p/w500/aDb548BOkFfI4nFm0kx8A3Ezh7H.jpg"
    ]
  },
  {
    id: "kriminal-drama",
    title: "Kriminal drama: Mashaqqatlar sari",
    count: "1 ta serial",
    href: "/collections/kriminal-drama",
    category: "theme",
    description: "Xayzenbergning metamfetamin imperiyasi — barcha davrlarning eng buyuk seriali.",
    posters: [
      "https://image.tmdb.org/t/p/w500/anFx9aTOOYqgS3v7x3R84Kz67ly.jpg",
      "https://image.tmdb.org/t/p/w500/anFx9aTOOYqgS3v7x3R84Kz67ly.jpg",
      "https://image.tmdb.org/t/p/w500/anFx9aTOOYqgS3v7x3R84Kz67ly.jpg"
    ]
  },
  {
    id: "fantastika-va-animatsiya",
    title: "Epik Fantastika va Animatsiya",
    count: "3 ta kino",
    href: "/collections/fantastika-va-animatsiya",
    category: "theme",
    description: "Avatar, Titanlar hujumi va Shrek 2 — dunyo e'tirofidagi eng sara durdonalar.",
    posters: [
      "https://image.tmdb.org/t/p/w500/wgwldDDlTDDMrluOMkpSA8lyKjv.jpg",
      "https://image.tmdb.org/t/p/w500/gKY6q7SjCkAU6FqvqWybDYgUKIF.jpg",
      "https://image.tmdb.org/t/p/w500/2yYP0PQjG8zVqturh1BAqu2Tixl.jpg"
    ]
  }
];
