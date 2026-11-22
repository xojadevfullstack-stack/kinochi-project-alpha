(function () {
  const KEY_FAVS = 'mediaplus_proto_favs';
  const KEY_HISTORY = 'mediaplus_proto_history';
  const KEY_REQUESTS = 'mediaplus_proto_requests';
  const KEY_VOTES = 'mediaplus_proto_votes';
  const KEY_REVIEWS = 'mediaplus_proto_reviews';

  const CATALOG = [
    {
      id: 1,
      code: '#1240',
      title: 'Dune: Part Two',
      subtitle: 'Dyuna: Ikkinchi qism (2024)',
      type: 'movies',
      typeLabel: 'FILM',
      genre: 'scifi',
      genreLabel: 'Fantastika',
      country: 'us',
      year: 2024,
      rating: 8.8,
      mpRating: 9.4,
      views: 12400,
      img: 'https://images.unsplash.com/photo-1626814026160-2237a95fc5a0?auto=format&fit=crop&w=600&q=80',
      desc: "Pol Atreydes va uning onasi Ledi Jessica Arrakisning Fremenlari safiga qo'shiladi. Pol o'z oilasini yo'q qilgan fitnachilardan qasos olish uchun kurashadi."
    },
    {
      id: 2,
      code: '#1103',
      title: 'Sherlock & Daughter',
      subtitle: 'Detektiv • 1-fasl, 8 qism (2025)',
      type: 'series',
      typeLabel: 'SERIAL',
      genre: 'drama',
      genreLabel: 'Detektiv',
      country: 'us',
      year: 2025,
      rating: 8.4,
      mpRating: 9.2,
      views: 9800,
      img: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=600&q=80',
      desc: "Mashhur izquvar Sherlok Xolms navbatdagi sirli jumboqlari bilan to'qnash keladi va kutilmagan hamkori bilan yangi fitnalarni fosh etadi."
    },
    {
      id: 3,
      code: '#1088',
      title: 'Chuqur (Çukur)',
      subtitle: 'Turk seriali • 4 fasl, 131 qism (2017-2021)',
      type: 'series',
      typeLabel: 'SERIAL',
      genre: 'drama',
      genreLabel: 'Kriminal',
      country: 'tr',
      year: 2023,
      rating: 8.3,
      mpRating: 9.6,
      views: 24500,
      img: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?auto=format&fit=crop&w=600&q=80',
      desc: "Istanbulning eng xavfli va sirli mahallalaridan biri bo'lgan «Chuqur» Ko'chovali oilasi nazorati ostida. Oilaning kenja o'g'li Yamach o'z ildizlariga qaytishga majbur bo'ladi."
    },
    {
      id: 4,
      code: '#1305',
      title: 'Akame ga Kill!',
      subtitle: 'Yaponiya • Jangari Anime (2024)',
      type: 'anime',
      typeLabel: 'ANIME',
      genre: 'action',
      genreLabel: 'Jangari',
      country: 'jp',
      year: 2024,
      rating: 8.2,
      mpRating: 9.0,
      views: 15300,
      img: 'https://images.unsplash.com/photo-1546776310-eef45dd6d63c?auto=format&fit=crop&w=600&q=80',
      desc: "Poytaxtdagi adolatsizlikka qarshi kurashuvchi maxfiy «Tungi reyd» guruhiga qo'shilgan yosh jangchi Tatsumining sarguzashtlari."
    },
    {
      id: 5,
      code: '#1410',
      title: "Uysiz ma'bud (Noragami)",
      subtitle: 'Noragami Aragoto • Fantastika Anime (2025)',
      type: 'anime',
      typeLabel: 'ANIME',
      genre: 'action',
      genreLabel: 'Fantastika',
      country: 'jp',
      year: 2025,
      rating: 8.1,
      mpRating: 8.9,
      views: 11200,
      img: 'https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?auto=format&fit=crop&w=600&q=80',
      desc: "Kambag'al xudo Yato oddiy qiz Hiyori bilan g'ayritabiiy sarguzashtlarga kirishadi va o'tmishdagi sirlar bilan to'qnashadi."
    },
    {
      id: 6,
      code: '#1199',
      title: 'Gladiator II',
      subtitle: 'Gladiator 2 • Tarixiy Jangari (2024)',
      type: 'movies',
      typeLabel: 'FILM',
      genre: 'action',
      genreLabel: 'Tarixiy',
      country: 'us',
      year: 2024,
      rating: 7.9,
      mpRating: 8.8,
      views: 18900,
      img: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80',
      desc: "Rim imperiyasining qudratli hukmdorlariga qarshi Kolizey arenasida adolat va shon-sharaf uchun jang qilayotgan Lyusiy hikoyasi."
    },
    {
      id: 7,
      code: '#1299',
      title: "Kalmar O'yini 2 (Squid Game)",
      subtitle: 'Janubiy Koreya • Triller Dorama (2024)',
      type: 'doramas',
      typeLabel: 'DORAMA',
      genre: 'thriller',
      genreLabel: 'Triller',
      country: 'kr',
      year: 2024,
      rating: 8.5,
      mpRating: 9.5,
      views: 35000,
      img: 'https://images.unsplash.com/photo-1509281373149-e957c6296406?auto=format&fit=crop&w=600&q=80',
      desc: "O'yinni yutib chiqqan Son Gi Xun sirli tashkilotni butunlay to'xtatish uchun yana halokatli musobaqaga qaytadi."
    },
    {
      id: 8,
      code: '#1255',
      title: 'Dominika (2024)',
      subtitle: 'Jangari Triller (2024)',
      type: 'movies',
      typeLabel: 'FILM',
      genre: 'action',
      genreLabel: 'Jangari',
      country: 'us',
      year: 2024,
      rating: 7.8,
      mpRating: 8.6,
      views: 8200,
      img: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=600&q=80',
      desc: "Tinch hayotni izlagan sobiq maxsus agent begunoh oilani himoya qilish uchun xalqaro jinoyat guruhiga qarshi yakka kurashga chiqadi."
    },
    {
      id: 9,
      code: '#1001',
      title: 'Oppenheimer',
      subtitle: 'Biografik Drama • Kristofer Nolan (2023)',
      type: 'movies',
      typeLabel: 'FILM',
      genre: 'drama',
      genreLabel: 'Biografiya',
      country: 'us',
      year: 2023,
      rating: 8.9,
      mpRating: 9.7,
      views: 42000,
      img: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?auto=format&fit=crop&w=600&q=80',
      desc: "Nazariy fizik Robert Oppengeymerning Manxetten loyihasidagi faoliyati va dunyoni o'zgartirgan kashfiyoti haqidagi tarixiy drama."
    },
    {
      id: 10,
      code: '#1140',
      title: 'Koralina sirli dunyoda',
      subtitle: 'Coraline • Animatsion Sarguzasht (2023)',
      type: 'cartoons',
      typeLabel: 'MULTFILM',
      genre: 'horror',
      genreLabel: 'Fantastika',
      country: 'us',
      year: 2023,
      rating: 8.4,
      mpRating: 9.1,
      views: 14500,
      img: 'https://images.unsplash.com/photo-1626814026160-2237a95fc5a0?auto=format&fit=crop&w=600&q=80',
      desc: "Yangi uyga ko'chgan qizaloq Koralina yashirin eshik ortidan o'z dunyosining sirli, ammo xavfli muqobilini kashf etadi."
    },
    {
      id: 11,
      code: '#1220',
      title: "Merosxo'rlar (The Heirs)",
      subtitle: 'Janubiy Koreya • Melodrama (2023)',
      type: 'doramas',
      typeLabel: 'DORAMA',
      genre: 'drama',
      genreLabel: 'Melodrama',
      country: 'kr',
      year: 2023,
      rating: 8.1,
      mpRating: 9.0,
      views: 19800,
      img: 'https://images.unsplash.com/photo-1546776310-eef45dd6d63c?auto=format&fit=crop&w=600&q=80',
      desc: "Badavlat imperiya vorislari tahsil oladigan elita maktabdagi sevgi, do'stlik va sinovlar haqidagi mashhur koreys doramasi."
    },
    {
      id: 12,
      code: '#1188',
      title: 'Sehrgarlar jangi (Jujutsu Kaisen)',
      subtitle: 'Yaponiya • Jangari Anime (2023)',
      type: 'anime',
      typeLabel: 'ANIME',
      genre: 'action',
      genreLabel: 'Jangari',
      country: 'jp',
      year: 2023,
      rating: 8.7,
      mpRating: 9.5,
      views: 31000,
      img: 'https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?auto=format&fit=crop&w=600&q=80',
      desc: "La'natlarga qarshi kurashuvchi sehrgarlar akademiyasi o'quvchisi Yuji Itadori insoniyatni qutqarish uchun kuchli qora kuch bilan kurashadi."
    },
    {
      id: 13,
      code: '#1050',
      title: 'Shrek 2',
      subtitle: 'Komediya Multfilm (2022)',
      type: 'cartoons',
      typeLabel: 'MULTFILM',
      genre: 'comedy',
      genreLabel: 'Komediya',
      country: 'us',
      year: 2022,
      rating: 8.3,
      mpRating: 9.3,
      views: 26000,
      img: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80',
      desc: "Shrek va malika Fiona Uzoq-uzoq qirollikdagi ota-onasining huzuriga borishadi va yangi quvnoq sarguzashtlarga duch kelishadi."
    },
    {
      id: 14,
      code: '#1330',
      title: 'Mehribon doktor (Good Doctor)',
      subtitle: 'Tibbiyot Drama • 1-fasl (2024)',
      type: 'doramas',
      typeLabel: 'DORAMA',
      genre: 'drama',
      genreLabel: 'Tibbiyot',
      country: 'kr',
      year: 2024,
      rating: 8.2,
      mpRating: 9.0,
      views: 14200,
      img: 'https://images.unsplash.com/photo-1509281373149-e957c6296406?auto=format&fit=crop&w=600&q=80',
      desc: "Noyob iste'dodga ega yosh jarrohning murakkab operatsiyalar va insoniy munosabatlar sinovidan o'tishi."
    },
    {
      id: 15,
      code: '#1355',
      title: 'Ajralish (Severance)',
      subtitle: 'Fantastik Triller • 2-fasl (2024)',
      type: 'series',
      typeLabel: 'SERIAL',
      genre: 'scifi',
      genreLabel: 'Triller',
      country: 'us',
      year: 2024,
      rating: 8.7,
      mpRating: 9.4,
      views: 21500,
      img: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=600&q=80',
      desc: "Ish va shaxsiy xotiralari jarrohlik yo'li bilan ajratilgan xodimlar sirli Lumon korporatsiyasi haqiqatini anglay boshlashadi."
    },
    {
      id: 16,
      code: '#1380',
      title: "Menga o'lim sovg'a qil",
      subtitle: "Death's Game • Fantastik Triller (2024)",
      type: 'doramas',
      typeLabel: 'DORAMA',
      genre: 'thriller',
      genreLabel: 'Fantastika',
      country: 'kr',
      year: 2024,
      rating: 8.6,
      mpRating: 9.3,
      views: 27400,
      img: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?auto=format&fit=crop&w=600&q=80',
      desc: "Umidsizlikka tushgan yigitga O'lim tomonidan 12 xil inson tanasida qayta yashash imkoniyati va og'ir sinov beriladi."
    },
    {
      id: 865,
      code: '#865',
      title: 'Resident Evil: Retribution',
      subtitle: 'Jangari Fantastika (2024)',
      type: 'movies',
      typeLabel: 'FILM',
      genre: 'action',
      genreLabel: 'Jangari',
      country: 'us',
      year: 2024,
      rating: 7.2,
      mpRating: 8.5,
      views: 16200,
      img: 'https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=600&q=80',
      desc: "Umbrella korporatsiyasining xavfli virusiga qarshi Elis yerosti majmuasidan qochish va omon qolish uchun jang qiladi."
    },
    {
      id: 201,
      code: '#2010',
      title: 'Yer va osmon jangchilari',
      subtitle: 'Fantastika Jangari (2024)',
      type: 'movies',
      typeLabel: 'FILM',
      genre: 'action',
      genreLabel: 'Jangari',
      country: 'us',
      year: 2024,
      rating: 7.7,
      mpRating: 8.6,
      views: 7400,
      img: 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&w=600&q=80',
      desc: "Yer va samoviy kuchlar to'qnashuvida dunyo muvozanatini saqlab qolishga bel bog'lagan jangchilar haqida epik film."
    },
    {
      id: 202,
      code: '#2011',
      title: 'Yarim stavkadagi Iblis',
      subtitle: '1-fasl • 8-qism (2024)',
      type: 'anime',
      typeLabel: 'ANIME',
      genre: 'comedy',
      genreLabel: 'Komediya',
      country: 'jp',
      year: 2024,
      rating: 8.0,
      mpRating: 8.8,
      views: 9100,
      img: 'https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?auto=format&fit=crop&w=600&q=80',
      desc: "Boshqa olamdan Tokioga tushib qolgan qahramon oddiy restoranda ishlab tirikchilik qilishga majbur bo'ladi."
    },
    {
      id: 203,
      code: '#2012',
      title: 'Misterium Marko effekti',
      subtitle: 'Detektiv Triller (2024)',
      type: 'movies',
      typeLabel: 'FILM',
      genre: 'thriller',
      genreLabel: 'Detektiv',
      country: 'us',
      year: 2024,
      rating: 7.9,
      mpRating: 8.7,
      views: 6800,
      img: 'https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?auto=format&fit=crop&w=600&q=80',
      desc: "Kutilmagan moliyaviy firibgarlik iziga tushgan tergovchi Karl Mork sirli «Marko effekti» ortidagi haqiqatni ochadi."
    }
  ];

  function readJson(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function writeJson(key, val) {
    try {
      localStorage.setItem(key, JSON.stringify(val));
    } catch (e) {}
  }

  function urlFor(item) {
    if (!item) return 'mockup_media_detail.html?id=1';
    if (item.type === 'series') return 'mockup_series_detail.html?id=' + item.id;
    return 'mockup_media_detail.html?id=' + item.id;
  }

  function getById(idOrCode) {
    const q = String(idOrCode || '').trim().toLowerCase();
    if (!q) return CATALOG[0];
    return (
      CATALOG.find(
        (x) => String(x.id) === q || x.code.toLowerCase() === q || ('#' + q) === x.code.toLowerCase()
      ) || CATALOG[0]
    );
  }

  function toast(msg) {
    let el = document.getElementById('mediaplusGlobalToast');
    if (!el) {
      el = document.createElement('div');
      el.id = 'mediaplusGlobalToast';
      el.className =
        'fixed top-16 left-1/2 -translate-x-1/2 -translate-y-4 opacity-0 pointer-events-none z-[130] px-4 py-2 rounded-2xl text-xs font-bold shadow-2xl border transition-all duration-300 flex items-center gap-2';
      document.body.appendChild(el);
    }
    const isLight = document.body.classList.contains('light-theme');
    el.style.backgroundColor = isLight ? 'rgba(255,255,255,0.96)' : 'rgba(18,20,29,0.95)';
    el.style.color = isLight ? '#0F172A' : '#FFFFFF';
    el.style.borderColor = 'rgba(229, 9, 20, 0.45)';
    el.style.backdropFilter = 'blur(16px)';
    el.innerHTML =
      '<span class="material-symbols-outlined text-[16px]" style="color:#E50914">check_circle</span><span>' +
      String(msg).replace(/</g, '&lt;') +
      '</span>';
    requestAnimationFrame(() => {
      el.classList.remove('-translate-y-4', 'opacity-0');
      el.classList.add('translate-y-0', 'opacity-100');
    });
    clearTimeout(el._timer);
    el._timer = setTimeout(() => {
      el.classList.add('-translate-y-4', 'opacity-0');
      el.classList.remove('translate-y-0', 'opacity-100');
    }, 2600);
  }

  function copyText(text, successMsg) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text);
      } else {
        const inp = document.createElement('textarea');
        inp.value = text;
        document.body.appendChild(inp);
        inp.select();
        document.execCommand('copy');
        document.body.removeChild(inp);
      }
    } catch (e) {}
    toast(successMsg || 'Nusxalandi ✓');
  }

  window.MediaPlusState = {
    getCatalog: () => CATALOG.slice(),
    getById,
    urlFor,
    randomItem: () => CATALOG[Math.floor(Math.random() * CATALOG.length)],
    getFavorites: () => readJson(KEY_FAVS, [1, 3]),
    isFavorite: (id) => readJson(KEY_FAVS, [1, 3]).includes(Number(id)),
    toggleFavorite: (id) => {
      const numId = Number(id);
      const favs = readJson(KEY_FAVS, [1, 3]);
      const idx = favs.indexOf(numId);
      const added = idx === -1;
      if (added) favs.unshift(numId);
      else favs.splice(idx, 1);
      writeJson(KEY_FAVS, favs);
      return added;
    },
    getHistory: () => readJson(KEY_HISTORY, [201, 202, 203, 1]),
    addHistory: (id) => {
      const numId = Number(id);
      if (!numId) return;
      const list = readJson(KEY_HISTORY, [201, 202, 203, 1]).filter((x) => x !== numId);
      list.unshift(numId);
      writeJson(KEY_HISTORY, list.slice(0, 20));
    },
    removeHistory: (id) => {
      const numId = Number(id);
      const list = readJson(KEY_HISTORY, [201, 202, 203, 1]).filter((x) => x !== numId);
      writeJson(KEY_HISTORY, list);
      return list;
    },
    clearHistory: () => writeJson(KEY_HISTORY, []),
    getRequests: () => readJson(KEY_REQUESTS, null),
    saveRequests: (arr) => writeJson(KEY_REQUESTS, arr),
    getVotes: () => readJson(KEY_VOTES, []),
    saveVotes: (arr) => writeJson(KEY_VOTES, arr),
    getReviews: (id) => readJson(KEY_REVIEWS + '_' + id, []),
    addReview: (id, rev) => {
      const list = readJson(KEY_REVIEWS + '_' + id, []);
      list.unshift(rev);
      writeJson(KEY_REVIEWS + '_' + id, list);
      return list;
    },
    toast,
    copyText,
    hydrateDetailPage: function () {
      const params = new URLSearchParams(window.location.search);
      const idParam = params.get('id');
      const item = idParam ? getById(idParam) : null;
      if (item) {
        window.MediaPlusState.addHistory(item.id);
        document.title = item.title + ' — MediaPlus';
        const stage = document.querySelector('section.cinema-stage');
        if (stage) {
          stage.querySelectorAll('h1').forEach((el) => (el.textContent = item.title));
          stage.querySelectorAll('h1 + p').forEach((el) => (el.textContent = item.subtitle));
          stage.querySelectorAll('img').forEach((img) => {
            img.src = item.img;
            img.alt = item.title;
          });
          stage.querySelectorAll('p.line-clamp-3').forEach((p) => (p.textContent = item.desc));
          stage.querySelectorAll('.font-mono.font-bold.text-brand-red').forEach((el) => {
            el.textContent = item.code;
          });
          stage.querySelectorAll('button[onclick*="copyCode"]').forEach((btn) => {
            btn.setAttribute('onclick', `copyCode('${item.code}')`);
          });
          const rawCode = item.code.replace('#', '');
          const prefix = item.type === 'series' ? 's_' : 'm_';
          stage.querySelectorAll('a[href*="MediaPlusOfficialBot?start="]').forEach((a) => {
            a.href = 'https://t.me/MediaPlusOfficialBot?start=' + prefix + rawCode;
          });
          const ratingEls = stage.querySelectorAll('.text-brand-gold');
          ratingEls.forEach((star) => {
            if (/\d+\.\d/.test(star.textContent || '')) {
              star.textContent = star.textContent.replace(/\d+\.\d/, String(item.rating));
            }
            const next = star.nextElementSibling;
            if (next && /\d+\.\d/.test(next.textContent || '')) {
              next.textContent = next.textContent.replace(/\d+\.\d/, String(item.rating));
            }
          });
        }
        const crumb = document.querySelector('.universal-breadcrumb span.font-semibold');
        if (crumb) crumb.textContent = item.title;
      }
      const activeId = item ? item.id : (window.location.pathname.includes('series') ? 3 : 1);
      window.__activeProtoItem = item || getById(activeId);
      const updateFavUI = (isFav) => {
        const favBtn = document.getElementById('favBtn');
        const favIcon = document.getElementById('favIcon');
        const favText = document.getElementById('favText');
        if (favBtn && favIcon && favText) {
          favBtn.classList.toggle('bg-brand-red', isFav);
          favBtn.classList.toggle('text-white', isFav);
          favBtn.classList.toggle('bg-[#141722]', !isFav);
          favBtn.classList.toggle('text-gray-300', !isFav);
          favIcon.textContent = isFav ? 'bookmark' : 'bookmark_border';
          favText.textContent = isFav ? 'Saqlandi' : 'Saqlash';
        }
        const favMob = document.getElementById('favBtnMob');
        if (favMob) {
          favMob.classList.toggle('bg-brand-red', isFav);
          favMob.classList.toggle('text-white', isFav);
          const spans = favMob.querySelectorAll('span');
          if (spans[0]) spans[0].textContent = isFav ? 'bookmark' : 'bookmark_border';
          if (spans[1]) spans[1].textContent = isFav ? 'Saqlandi' : 'Saqlash';
        }
      };
      updateFavUI(window.MediaPlusState.isFavorite(window.__activeProtoItem.id));
      window.__syncProtoFavUI = updateFavUI;
    },
    isLowEndDevice: () => {
      try {
        const nav = navigator || {};
        const conn = nav.connection || nav.mozConnection || nav.webkitConnection;
        if (conn && conn.saveData) return true;
        if (typeof nav.deviceMemory === 'number' && nav.deviceMemory <= 2) return true;
        if (typeof nav.hardwareConcurrency === 'number' && nav.hardwareConcurrency <= 2) return true;
        if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
          return true;
        }
      } catch (e) {}
      return false;
    },
    resetAll: () => {
      try {
        [KEY_FAVS, KEY_HISTORY, KEY_REQUESTS, KEY_VOTES].forEach((k) => localStorage.removeItem(k));
        Object.keys(localStorage).forEach((k) => {
          if (k.startsWith(KEY_REVIEWS) || k.startsWith('mediaplus_mockup_tour_')) {
            localStorage.removeItem(k);
          }
        });
      } catch (e) {}
    }
  };

  /**
   * Native OS / Hardware Back button handler for mobile browsers.
   * When any modal, drawer (#mainSidebar), or onboarding tour is open,
   * intercepts popstate to close the topmost overlay cleanly instead of leaving the page,
   * and pops its history sentinel if the user closed the overlay manually.
   */
  function setupNativeBackSupport() {
    if (window.__mpNativeBackReady) return;
    window.__mpNativeBackReady = true;

    const overlays = [
      {
        id: 'onboardingRoot',
        isOpen: (el) => !el.classList.contains('hidden'),
        close: () => {
          if (typeof window.finishOnboardingTour === 'function') return window.finishOnboardingTour();
          const el = document.getElementById('onboardingRoot');
          if (el) el.classList.add('hidden');
        }
      },
      {
        id: 'trailerModal',
        isOpen: (el) => !el.classList.contains('hidden'),
        close: () => {
          if (typeof window.closeTrailerModal === 'function') return window.closeTrailerModal();
          if (typeof window.closeTrailer === 'function') return window.closeTrailer();
          const iframe = document.getElementById('trailerIframe');
          if (iframe) iframe.src = '';
          const el = document.getElementById('trailerModal');
          if (el) {
            el.classList.add('hidden');
            el.classList.remove('flex');
          }
        }
      },
      {
        id: 'reportModal',
        isOpen: (el) => !el.classList.contains('hidden'),
        close: () => {
          if (typeof window.closeReportModal === 'function') return window.closeReportModal();
          const el = document.getElementById('reportModal');
          if (el) el.classList.add('hidden');
        }
      },
      {
        id: 'filmographyModal',
        isOpen: (el) => !el.classList.contains('hidden'),
        close: () => {
          if (typeof window.closeFilmography === 'function') return window.closeFilmography();
          const el = document.getElementById('filmographyModal');
          if (el) el.classList.add('hidden');
        }
      },
      {
        id: 'requestModal',
        isOpen: (el) => !el.classList.contains('hidden'),
        close: () => {
          if (typeof window.closeRequestModal === 'function') return window.closeRequestModal();
          const el = document.getElementById('requestModal');
          if (el) {
            el.classList.add('hidden');
            el.classList.remove('flex');
          }
        }
      },
      {
        id: 'mainSidebar',
        isOpen: (el) => !el.classList.contains('-translate-x-full'),
        close: () => {
          if (typeof window.toggleSidebar === 'function') return window.toggleSidebar();
          const el = document.getElementById('mainSidebar');
          if (el) el.classList.add('-translate-x-full');
          const bd = document.getElementById('sidebarBackdrop');
          if (bd) bd.classList.add('hidden');
        }
      }
    ];

    const getOpenOverlays = () =>
      overlays.filter((cfg) => {
        const el = document.getElementById(cfg.id);
        return el && cfg.isOpen(el);
      });

    let closingFromPop = false;
    let ignoringNextPop = false;
    let cleanupTimer = null;

    const syncHistoryWithOverlays = () => {
      if (cleanupTimer) {
        clearTimeout(cleanupTimer);
        cleanupTimer = null;
      }
      if (closingFromPop) return;

      const open = getOpenOverlays();
      const currentState = window.history.state || {};
      if (open.length > 0) {
        if (!currentState.__mpOverlay) {
          window.history.pushState({ ...currentState, __mpOverlay: open[0].id }, '');
        } else if (currentState.__mpOverlay !== open[0].id) {
          window.history.replaceState({ ...currentState, __mpOverlay: open[0].id }, '');
        }
      } else if (currentState.__mpOverlay) {
        cleanupTimer = setTimeout(() => {
          if (getOpenOverlays().length === 0 && window.history.state && window.history.state.__mpOverlay) {
            ignoringNextPop = true;
            window.history.back();
          }
        }, 45);
      }
    };

    window.addEventListener('popstate', () => {
      if (ignoringNextPop) {
        ignoringNextPop = false;
        return;
      }
      const open = getOpenOverlays();
      if (open.length === 0) return;

      closingFromPop = true;
      try {
        open[0].close();
      } finally {
        const stillOpen = getOpenOverlays();
        if (stillOpen.length > 0) {
          window.history.pushState({ ...(window.history.state || {}), __mpOverlay: stillOpen[0].id }, '');
        }
        Promise.resolve().then(() => {
          closingFromPop = false;
        });
      }
    });

    const attachObservers = () => {
      const observer = new MutationObserver(syncHistoryWithOverlays);
      overlays.forEach((cfg) => {
        const el = document.getElementById(cfg.id);
        if (el) {
          observer.observe(el, { attributes: true, attributeFilter: ['class'] });
        }
      });
      if (getOpenOverlays().length > 0) syncHistoryWithOverlays();
    };

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', attachObservers, { once: true });
    } else {
      attachObservers();
    }
  }

  function setupLowEndPerformance() {
    if (typeof document === 'undefined') return;
    try {
      if (window.MediaPlusState && window.MediaPlusState.isLowEndDevice()) {
        document.documentElement.classList.add('low-end-device');
      }
      if (!document.getElementById('mp-perf-optimizations') && document.head) {
        const style = document.createElement('style');
        style.id = 'mp-perf-optimizations';
        style.textContent = [
          'footer { content-visibility: auto; contain-intrinsic-size: 1px 280px; }',
          'main section:nth-of-type(n+3) { content-visibility: auto; contain-intrinsic-size: 1px 360px; }',
          'html.low-end-device header, html.low-end-device nav.fixed, html.low-end-device #mainSidebar, html.low-end-device .apple-glass, html.low-end-device [class*="backdrop-blur"], html.low-end-device [style*="backdrop-filter"] { -webkit-backdrop-filter: none !important; backdrop-filter: none !important; }',
          'html.low-end-device header, html.low-end-device #mainSidebar { background-color: rgba(11, 13, 18, 0.96) !important; }',
          'html.low-end-device body.light-theme header, html.low-end-device body.light-theme #mainSidebar { background-color: rgba(255, 255, 255, 0.97) !important; }',
          'html.low-end-device nav.fixed { background-color: rgba(14, 16, 22, 0.96) !important; }',
          'html.low-end-device body.light-theme nav.fixed { background-color: rgba(255, 255, 255, 0.97) !important; }',
          'html.low-end-device [class*="shadow-2xl"], html.low-end-device [class*="shadow-xl"] { box-shadow: 0 6px 16px rgba(0, 0, 0, 0.36) !important; }',
          'html.low-end-device [class*="animate-marquee"], html.low-end-device .marquee-track { animation: none !important; will-change: auto !important; overflow-x: auto; }',
          '@media (prefers-reduced-motion: reduce) { [class*="animate-marquee"], .marquee-track, .animate-pulse, .animate-bounce, .animate-ping { animation: none !important; will-change: auto !important; } }'
        ].join('\n');
        document.head.appendChild(style);
      }
      const upgradeImages = () => {
        document.querySelectorAll('img').forEach((img) => {
          if (!img.hasAttribute('decoding')) img.setAttribute('decoding', 'async');
          const id = img.id || '';
          const src = img.getAttribute('src') || '';
          const isPriority = /hero|logo/i.test(id) || /logo-mediaplus/i.test(src);
          if (!isPriority && !img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
          }
        });
      };
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', upgradeImages, { once: true });
      } else {
        upgradeImages();
      }
    } catch (e) {}
  }

  setupLowEndPerformance();
  setupNativeBackSupport();
})();
