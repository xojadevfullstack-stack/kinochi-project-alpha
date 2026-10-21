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
    id: "superheroes",
    title: "Superqahramonlar haqida kinolar",
    count: "121 ta kino",
    href: "/collections?theme=superheroes",
    category: "theme",
    description: "Marvel, DC va barcha qahramonlar to'plami.",
    posters: [
      "https://image.tmdb.org/t/p/w500/yF1eOkaYvwiORauRCPWznV9xVvi.jpg",
      "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg",
      "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg"
    ]
  },
  {
    id: "netflix-series",
    title: "Netflix seriallari va kinolari",
    count: "38 ta kino",
    href: "/series?category=netflix",
    category: "theme",
    description: "Jahon trendidagi eng sara Netflix loyihalari.",
    posters: [
      "https://image.tmdb.org/t/p/w500/dDlEmu3EZ0Pgg93K2SVNLCjCSvE.jpg",
      "https://image.tmdb.org/t/p/w500/7vjaCdMw15FEbXyLQTVa04URsPm.jpg",
      "https://image.tmdb.org/t/p/w500/reKs8y4m54gq4zP1gJ8a2BsmHlU.jpg"
    ]
  },
  {
    id: "wizards",
    title: "Sehrgarlar haqida kinolar",
    count: "41 ta kino",
    href: "/collections/garri-potter",
    category: "franchise",
    description: "Xogvarts sehrgarlari va sehrli afsungarlar olami.",
    posters: [
      "https://image.tmdb.org/t/p/w500/wuMc08IPKEatf9rnMNXvIDxqP4W.jpg",
      "https://image.tmdb.org/t/p/w500/sdEOH0992YZ0QSxgXNIGLq1ToUi.jpg",
      "https://image.tmdb.org/t/p/w500/fECBtHlr0RB3foNHDiCBXeg9Bv9.jpg"
    ]
  },
  {
    id: "vampires",
    title: "Vampirlar haqida kinolar",
    count: "39 ta kino",
    href: "/catalog?genre=horror",
    category: "theme",
    description: "Qonxo'rlar va tunda yashovchilar sarguzashtlari.",
    posters: [
      "https://image.tmdb.org/t/p/w500/wVYREutTvI2tmxr6ujrHT704wGF.jpg",
      "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
      "https://image.tmdb.org/t/p/w500/5aMm9k5jO9YhYw65fM7U4m2G5g.jpg"
    ]
  },
  {
    id: "dragons",
    title: "Ajdarlar haqida kinolar",
    count: "21 ta kino",
    href: "/catalog?genre=scifi",
    category: "theme",
    description: "Afsonaviy olov purkovchi bahaybat maxluqlar.",
    posters: [
      "https://image.tmdb.org/t/p/w500/kOVEVeg59E0wsnXmF9nBY61Om61.jpg",
      "https://image.tmdb.org/t/p/w500/qAZ0whky09bptYBPumwF8QZ4p9K.jpg",
      "https://image.tmdb.org/t/p/w500/xg27NrXi79CGUrsqayuh5914023.jpg"
    ]
  },
  {
    id: "werewolves",
    title: "Odam-bo'rilar haqida kinolar",
    count: "14 ta kino",
    href: "/catalog?genre=horror",
    category: "theme",
    description: "To'lin oy tunda sodir bo'ladigan qo'rqinchli o'zgarishlar.",
    posters: [
      "https://image.tmdb.org/t/p/w500/bTeQ9u1j307m82mX3K2Q9r8g1m.jpg",
      "https://image.tmdb.org/t/p/w500/4D0PpNI0km5GR7u1imWmxME4Pq5.jpg",
      "https://image.tmdb.org/t/p/w500/whNwkEQYWLFJA8ij00Ke24TN9Y7.jpg"
    ]
  },
  {
    id: "zombies",
    title: "Zombi haqida kinolar",
    count: "37 ta kino",
    href: "/catalog?genre=horror",
    category: "theme",
    description: "Apokalipsis va tirik murdalar o'rtasidagi omon qolish jangi.",
    posters: [
      "https://image.tmdb.org/t/p/w500/reKs8y4m54gq4zP1gJ8a2BsmHlU.jpg",
      "https://image.tmdb.org/t/p/w500/sdEOH0992YZ0QSxgXNIGLq1ToUi.jpg",
      "https://image.tmdb.org/t/p/w500/wuMc08IPKEatf9rnMNXvIDxqP4W.jpg"
    ]
  },
  {
    id: "gladiators",
    title: "Gladiatorlar va Qadimgi Rim haqida",
    count: "20 ta kino",
    href: "/catalog?genre=history",
    category: "theme",
    description: "Qadimgi imperiyalar jangi, kolizey va jasur qahramonlar.",
    posters: [
      "https://image.tmdb.org/t/p/w500/ty8TGRuvJLPUmAR1H1nRIsgwvim.jpg",
      "https://image.tmdb.org/t/p/w500/8qB95557xV9qN955.jpg",
      "https://image.tmdb.org/t/p/w500/yF1eOkaYvwiORauRCPWznV9xVvi.jpg"
    ]
  },
  {
    id: "mafia",
    title: "Mafiya va gangsterlar haqida kinolar",
    count: "62 ta kino",
    href: "/collections?theme=mafia",
    category: "theme",
    description: "Kriminal olam, yashirin jinoiy to'dalar va oilaviy qoidalar.",
    posters: [
      "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
      "https://image.tmdb.org/t/p/w500/hek3koDUyRQk7FIhPXsa6mT2Zc3.jpg",
      "https://image.tmdb.org/t/p/w500/whNwkEQYWLFJA8ij00Ke24TN9Y7.jpg"
    ]
  },
  {
    id: "video-games",
    title: "Kompyuter o'yinlari asosidagi kinolar",
    count: "38 ta kino",
    href: "/collections?theme=games",
    category: "theme",
    description: "Sonik, Mario, Mortal Kombat va eng mashhur geymer filmlari.",
    posters: [
      "https://image.tmdb.org/t/p/w500/a26cQPRBh3xFuKoKf0Ki87GQUhO.jpg",
      "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
      "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg"
    ]
  },
  {
    id: "monsters",
    title: "Ulkan maxluqlar haqida kinolar",
    count: "20 ta kino",
    href: "/collections?theme=monsters",
    category: "theme",
    description: "Godzilladan tortib King Konggacha bahaybat maxluqlar to'qnashuvi.",
    posters: [
      "https://image.tmdb.org/t/p/w500/tMefBSflR6PGQLv7WvFPpKLZkyk.jpg",
      "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg",
      "https://image.tmdb.org/t/p/w500/yF1eOkaYvwiORauRCPWznV9xVvi.jpg"
    ]
  },
  {
    id: "prison",
    title: "Qamoqxona va qochish haqida kinolar",
    count: "42 ta kino",
    href: "/catalog?genre=crime",
    category: "theme",
    description: "Shoushenkdan qochish, Boika va qattiq tartibli qamoqxonalar.",
    posters: [
      "https://image.tmdb.org/t/p/w500/9cqN0LHpH7WbgZqhJ3Z5b2b9V5u.jpg",
      "https://image.tmdb.org/t/p/w500/whNwkEQYWLFJA8ij00Ke24TN9Y7.jpg",
      "https://image.tmdb.org/t/p/w500/8qB95557xV9qN955.jpg"
    ]
  }
];
