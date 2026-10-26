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
    href: "/catalog?genre=action",
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
    href: "/series",
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
      "https://image.tmdb.org/t/p/w500/1XDDXPXGiI8id7MrUxK36ke7gkX.jpg",
      "https://image.tmdb.org/t/p/w500/ygGmAO60t8GyqUo9xYeYxSZAR3b.jpg",
      "https://image.tmdb.org/t/p/w500/xT98tLqatZPQApyRml42QTC5j5.jpg"
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
      "https://image.tmdb.org/t/p/w500/3Gkb6jm6962ADUP99ZGJ9H90Ghn.jpg",
      "https://image.tmdb.org/t/p/w500/6v7F3rM6B3aK6g7M2jV4sR9pL1n.jpg",
      "https://image.tmdb.org/t/p/w500/bQLA5i60Uj64GjWbI753bM754jX.jpg"
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
      "https://image.tmdb.org/t/p/w500/vVpEOvdxVBP25VZa69DTcBa56IT.jpg",
      "https://image.tmdb.org/t/p/w500/haMw5q5X4Nqj9L2k26ZgE9E8G2j.jpg",
      "https://image.tmdb.org/t/p/w500/n7PVu0hSz2sAsVekSSio1kWmrss.jpg"
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
      "https://image.tmdb.org/t/p/w500/2cxhvwyEwRlysAmRH4iodkvo0z5.jpg",
      "https://image.tmdb.org/t/p/w500/spW44FpI3jU2sB10R8l0bS0hDqX.jpg",
      "https://image.tmdb.org/t/p/w500/aA21tU0g5wWb7oM7d4B6zP7bZ4s.jpg"
    ]
  },
  {
    id: "mafia",
    title: "Mafiya va gangsterlar haqida kinolar",
    count: "62 ta kino",
    href: "/catalog?genre=crime",
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
    href: "/catalog?genre=adventure",
    category: "theme",
    description: "Sonik, Mario, Mortal Kombat va eng mashhur geymer filmlari.",
    posters: [
      "https://image.tmdb.org/t/p/w500/a26cQPRBh3xFuKoKf0Ki87GQUhO.jpg",
      "https://image.tmdb.org/t/p/w500/qNBAXBIQlnOThrVvA6mA2B5ggV6.jpg",
      "https://image.tmdb.org/t/p/w500/9yBVqNruk6KkrxwtqURnSTj5x6v.jpg"
    ]
  },
  {
    id: "monsters",
    title: "Ulkan maxluqlar haqida kinolar",
    count: "20 ta kino",
    href: "/catalog?genre=scifi",
    category: "theme",
    description: "Godzilladan tortib King Konggacha bahaybat maxluqlar to'qnashuvi.",
    posters: [
      "https://image.tmdb.org/t/p/w500/tMefBSflR6PGQLv7WvFPpKLZkyk.jpg",
      "https://image.tmdb.org/t/p/w500/phmj17e3fT4x5gB82iF1l6uWb8N.jpg",
      "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg"
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
      "https://image.tmdb.org/t/p/w500/lyQBXzOQSuE59IsHyhrp0qIiPAz.jpg",
      "https://image.tmdb.org/t/p/w500/bQLA5i60Uj64GjWbI753bM754jX.jpg",
      "https://image.tmdb.org/t/p/w500/6v7F3rM6B3aK6g7M2jV4sR9pL1n.jpg"
    ]
  }
];
