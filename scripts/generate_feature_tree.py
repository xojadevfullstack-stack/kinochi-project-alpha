# -*- coding: utf-8 -*-
"""
Kinochi Project - Full Feature Tree Generator
Produces high-resolution SVG and interactive HTML preview for Website, Bot, and Admin Panel.
"""
import os

svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1860 1440" width="100%" height="100%" style="background-color: #060913; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <defs>
    <!-- Gradients -->
    <linearGradient id="header-bg" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#E50914" stop-opacity="0.35"/>
      <stop offset="50%" stop-color="#0284C7" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#059669" stop-opacity="0.3"/>
    </linearGradient>
    <linearGradient id="col-bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#111827" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#0B0F19" stop-opacity="0.98"/>
    </linearGradient>
    <linearGradient id="card-inner" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#161F33" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#0D1322" stop-opacity="0.95"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.5"/>
    </filter>
  </defs>

  <!-- ==================== HEADER ==================== -->
  <g filter="url(#shadow)">
    <rect x="30" y="20" width="1800" height="80" rx="14" fill="url(#col-bg)" stroke="#1F2937" stroke-width="1.5" />
    <rect x="30" y="20" width="1800" height="80" rx="14" fill="url(#header-bg)" />
    <rect x="55" y="38" width="6" height="44" rx="3" fill="#E50914" />
    <text x="75" y="55" fill="#FFFFFF" font-size="20" font-weight="800" letter-spacing="0.5">KINOCHI / MEDIAPLUS — BARCHA FUNKSIYALAR, TUGMALAR VA MODALLAR DARAXTI (TREE VIEW)</text>
    <text x="75" y="80" fill="#94A3B8" font-size="13">Websayt (25 sahifa), Telegram Bot (Thin Client) va Admin Panel (19 bo'lim) barcha ichki tugmalari [Btn], modallari va maydonlari</text>
  </g>

  <!-- ========================================================================= -->
  <!-- USTUN 1: WEBSAYT (X: 30, Width: 580)                                       -->
  <!-- ========================================================================= -->
  <g transform="translate(30, 120)">
    <rect x="0" y="0" width="580" height="1290" rx="14" fill="url(#col-bg)" stroke="#0284C7" stroke-width="1.8" filter="url(#shadow)"/>
    
    <!-- Title Badge -->
    <rect x="20" y="18" width="540" height="42" rx="8" fill="#082F49" stroke="#38BDF8" stroke-width="1.2" />
    <text x="35" y="45" fill="#38BDF8" font-size="15" font-weight="800">🌐 1. WEBSAYT (Next.js 14 App Router, Web Portal)</text>

    <!-- Node 1.1: Bosh sahifa -->
    <g transform="translate(20, 75)">
      <rect x="0" y="0" width="540" height="240" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🏠 1.1 Bosh sahifa (/)</text>
      
      <!-- Sub-items -->
      <text x="25" y="52" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🎬 Hero Banner:</text>
      <rect x="155" y="40" width="115" height="20" rx="4" fill="#0284C7" /><text x="160" y="54" fill="#FFF" font-size="9.5" font-weight="700">[Btn: Tomosha qilish]</text>
      <rect x="276" y="40" width="75" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="281" y="54" fill="#CBD5E1" font-size="9.5">[Btn: Treyler]</text>
      <rect x="357" y="40" width="85" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="362" y="54" fill="#CBD5E1" font-size="9.5">[Btn: + Sevimlilar]</text>

      <text x="25" y="85" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🔊 Ambient Trailer:</text>
      <rect x="165" y="73" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="87" fill="#CBD5E1" font-size="9.5">[Btn: Mute / Unmute]</text>
      <rect x="286" y="73" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="291" y="87" fill="#CBD5E1" font-size="9.5">[Fallback: Rasm/Poster]</text>

      <text x="25" y="118" fill="#38BDF8" font-size="11.5" font-weight="600">├── ⏱️ Continue Watching:</text>
      <rect x="175" y="106" width="75" height="20" rx="4" fill="#065F46" /><text x="180" y="120" fill="#34D399" font-size="9.5">[Bar: % ko'rildi]</text>
      <rect x="256" y="106" width="115" height="20" rx="4" fill="#0284C7" /><text x="261" y="120" fill="#FFF" font-size="9.5">[Btn: Davom ettirish]</text>
      <rect x="377" y="106" width="75" height="20" rx="4" fill="#450A0A" /><text x="382" y="120" fill="#F87171" font-size="9.5">[Btn: ✕ O'chirish]</text>

      <text x="25" y="151" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🎞️ Carousel &amp; Lenta:</text>
      <rect x="165" y="139" width="65" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="153" fill="#CBD5E1" font-size="9.5">[Btn: ◀ Oldingi]</text>
      <rect x="236" y="139" width="65" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="241" y="153" fill="#CBD5E1" font-size="9.5">[Btn: Keyingi ▶]</text>
      <rect x="307" y="139" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="312" y="153" fill="#CBD5E1" font-size="9.5">[Btn: Barchasi &gt;]</text>

      <text x="25" y="184" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🏆 Top 100 reyting bloki:</text>
      <text x="185" y="184" fill="#94A3B8" font-size="10.5">IMDb &amp; Kinopoisk reyting ballari va tartibi</text>

      <text x="25" y="217" fill="#38BDF8" font-size="11.5" font-weight="600">└── 🧭 Navigatsiya &amp; Header:</text>
      <rect x="185" y="205" width="85" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="190" y="219" fill="#CBD5E1" font-size="9.5">[Link: Filmlar]</text>
      <rect x="276" y="205" width="85" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="281" y="219" fill="#CBD5E1" font-size="9.5">[Link: Seriallar]</text>
      <rect x="367" y="205" width="75" height="20" rx="4" fill="#0284C7" /><text x="372" y="219" fill="#FFF" font-size="9.5">[Btn: Kirish]</text>
    </g>

    <!-- Node 1.2: Film & Serial Pleyer -->
    <g transform="translate(20, 330)">
      <rect x="0" y="0" width="540" height="260" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🎬 1.2 Film &amp; Serial Sahifasi (/movie/[id], /serial/[id])</text>
      
      <text x="25" y="52" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🎥 Video Player:</text>
      <rect x="145" y="40" width="80" height="20" rx="4" fill="#0284C7" /><text x="150" y="54" fill="#FFF" font-size="9.5">[Btn: Play/Pause]</text>
      <rect x="231" y="40" width="60" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="236" y="54" fill="#CBD5E1" font-size="9.5">[Btn: -10s]</text>
      <rect x="297" y="40" width="60" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="302" y="54" fill="#CBD5E1" font-size="9.5">[Btn: +10s]</text>
      <rect x="363" y="40" width="75" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="368" y="54" fill="#CBD5E1" font-size="9.5">[Btn: Fullscreen]</text>

      <text x="25" y="85" fill="#38BDF8" font-size="11.5" font-weight="600">├── ⚙️ Player sozlamalari:</text>
      <rect x="165" y="73" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="87" fill="#F59E0B" font-size="9.5">[Drop: 360-1080p]</text>
      <rect x="276" y="73" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="281" y="87" fill="#38BDF8" font-size="9.5">[Drop: Tezlik 0.5-2x]</text>
      <rect x="387" y="73" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="392" y="87" fill="#CBD5E1" font-size="9.5">[Drop: Ovoz/Sub]</text>

      <text x="25" y="118" fill="#38BDF8" font-size="11.5" font-weight="600">├── 📑 Serial bo'limi:</text>
      <rect x="145" y="106" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="150" y="120" fill="#CBD5E1" font-size="9.5">[Tab: Mavsum 1, 2...]</text>
      <rect x="256" y="106" width="125" height="20" rx="4" fill="#065F46" /><text x="261" y="120" fill="#34D399" font-size="9.5">[Grid: 1, 2, 3... qismlar]</text>

      <text x="25" y="151" fill="#38BDF8" font-size="11.5" font-weight="600">├── ⭐ Baholash &amp; Fikr:</text>
      <rect x="165" y="139" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="153" fill="#F59E0B" font-size="9.5">[Stars: 1..10 yulduz]</text>
      <rect x="276" y="139" width="95" height="20" rx="4" fill="#0284C7" /><text x="281" y="153" fill="#FFF" font-size="9.5">[Btn: Fikr yozish]</text>
      <rect x="377" y="139" width="85" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="382" y="153" fill="#CBD5E1" font-size="9.5">[Btn: Like/Dislike]</text>

      <text x="25" y="184" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🔗 Ulashish &amp; Bot:</text>
      <rect x="155" y="172" width="125" height="20" rx="4" fill="#0284C7" /><text x="160" y="186" fill="#FFF" font-size="9.5">[Btn: Telegramda ko'rish]</text>
      <rect x="286" y="172" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="291" y="186" fill="#CBD5E1" font-size="9.5">[Btn: Nusxa olish]</text>

      <text x="25" y="217" fill="#38BDF8" font-size="11.5" font-weight="600">└── 🚨 Shikoyat &amp; Muammo:</text>
      <rect x="175" y="205" width="115" height="20" rx="4" fill="#450A0A" stroke="#DC2626" /><text x="180" y="219" fill="#F87171" font-size="9.5">[Btn: Xabar berish]</text>
      <rect x="296" y="205" width="155" height="20" rx="4" fill="#1E293B" /><text x="301" y="219" fill="#CBD5E1" font-size="9.5">[Modal: Shikoyat sababi]</text>
    </g>

    <!-- Node 1.3: Qidiruv & Filtrlar -->
    <g transform="translate(20, 605)">
      <rect x="0" y="0" width="540" height="210" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🔍 1.3 Katalog &amp; Aqlli Qidiruv (/search, /catalog)</text>

      <text x="25" y="52" fill="#38BDF8" font-size="11.5" font-weight="600">├── ⌨️ Qidiruv satri:</text>
      <rect x="145" y="40" width="165" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="150" y="54" fill="#CBD5E1" font-size="9.5">[Input: Film, aktyor nomi...]</text>
      <rect x="316" y="40" width="75" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="321" y="54" fill="#CBD5E1" font-size="9.5">[Btn: Tozalash]</text>

      <text x="25" y="85" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🎛️ Ko'p bosqichli filtr:</text>
      <rect x="165" y="73" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="87" fill="#CBD5E1" font-size="9.5">[Drop: Janrlar]</text>
      <rect x="266" y="73" width="85" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="271" y="87" fill="#CBD5E1" font-size="9.5">[Drop: Yillar]</text>
      <rect x="357" y="73" width="85" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="362" y="87" fill="#CBD5E1" font-size="9.5">[Drop: Davlat]</text>

      <text x="25" y="118" fill="#38BDF8" font-size="11.5" font-weight="600">├── 📊 Saralash (Sort):</text>
      <rect x="155" y="106" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="160" y="120" fill="#38BDF8" font-size="9.5">[Btn: Eng so'nggi]</text>
      <rect x="266" y="106" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="271" y="120" fill="#F59E0B" font-size="9.5">[Btn: Reyting]</text>
      <rect x="367" y="106" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="372" y="120" fill="#CBD5E1" font-size="9.5">[Btn: Ko'rishlar]</text>

      <text x="25" y="151" fill="#38BDF8" font-size="11.5" font-weight="600">└── 📑 Natijalar paneli:</text>
      <rect x="155" y="139" width="115" height="20" rx="4" fill="#0284C7" /><text x="160" y="153" fill="#FFF" font-size="9.5">[Btn: Ko'proq yuklash]</text>
      <rect x="276" y="139" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="281" y="153" fill="#CBD5E1" font-size="9.5">[Btn: Sahifa 1, 2, 3..]</text>
    </g>

    <!-- Node 1.4: Shaxsiy kabinet & Boshqalar -->
    <g transform="translate(20, 830)">
      <rect x="0" y="0" width="540" height="210" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">👤 1.4 Foydalanuvchi Kabineti (/profile, /favorites)</text>

      <text x="25" y="52" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🕒 Tarix (/history):</text>
      <rect x="155" y="40" width="125" height="20" rx="4" fill="#450A0A" stroke="#DC2626" /><text x="160" y="54" fill="#F87171" font-size="9.5">[Btn: Tarixni tozalash]</text>
      <rect x="286" y="40" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="291" y="54" fill="#CBD5E1" font-size="9.5">[Btn: Qatorni o'chirish]</text>

      <text x="25" y="85" fill="#38BDF8" font-size="11.5" font-weight="600">├── ⭐ Sevimlilar (/favorites):</text>
      <rect x="175" y="73" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="180" y="87" fill="#CBD5E1" font-size="9.5">[Btn: Ro'yxatdan ol]</text>
      <rect x="286" y="73" width="95" height="20" rx="4" fill="#0284C7" /><text x="291" y="87" fill="#FFF" font-size="9.5">[Btn: Hammasi]</text>

      <text x="25" y="118" fill="#38BDF8" font-size="11.5" font-weight="600">├── ⚙️ Profil Sozlamalari:</text>
      <rect x="165" y="106" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="120" fill="#CBD5E1" font-size="9.5">[Drop: Til UZ/RU]</text>
      <rect x="266" y="106" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="271" y="120" fill="#CBD5E1" font-size="9.5">[Toggle: Tungi rejim]</text>

      <text x="25" y="151" fill="#38BDF8" font-size="11.5" font-weight="600">└── 🚪 Akkaunt amallari:</text>
      <rect x="165" y="139" width="105" height="20" rx="4" fill="#450A0A" /><text x="170" y="153" fill="#F87171" font-size="9.5">[Btn: Chiqish (Logout)]</text>
      <rect x="276" y="139" width="125" height="20" rx="4" fill="#0284C7" /><text x="281" y="153" fill="#FFF" font-size="9.5">[Btn: Telegram bog'lash]</text>
    </g>

    <!-- Node 1.5: Yordamchi sahifalar -->
    <g transform="translate(20, 1055)">
      <rect x="0" y="0" width="540" height="210" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">📑 1.5 Yordamchi &amp; Qo'shimcha Sahifalar</text>

      <text x="25" y="52" fill="#38BDF8" font-size="11.5" font-weight="600">├── 📦 To'plamlar (/collections):</text>
      <rect x="185" y="40" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="190" y="54" fill="#CBD5E1" font-size="9.5">[Btn: To'plamni ko'rish]</text>
      <rect x="306" y="40" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="311" y="54" fill="#CBD5E1" font-size="9.5">[Btn: Xronologiya]</text>

      <text x="25" y="85" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🎭 Aktyorlar (/actors/[id]):</text>
      <text x="185" y="85" fill="#94A3B8" font-size="10.5">Biografiya, suratlar, ishtirok etgan filmlari</text>

      <text x="25" y="118" fill="#38BDF8" font-size="11.5" font-weight="600">├── 🔔 Bildirishnomalar (/notifications):</text>
      <rect x="205" y="106" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="210" y="120" fill="#CBD5E1" font-size="9.5">[Btn: O'qildi belgilash]</text>

      <text x="25" y="151" fill="#38BDF8" font-size="11.5" font-weight="600">└── 🔒 Xavfsizlik &amp; Diagnostika:</text>
      <rect x="185" y="139" width="135" height="20" rx="4" fill="#450A0A" /><text x="190" y="153" fill="#F87171" font-size="9.5">[DevOnly: /test-auth]</text>
      <rect x="326" y="139" width="105" height="20" rx="4" fill="#1E293B" /><text x="331" y="153" fill="#CBD5E1" font-size="9.5">[Btn: 404 / 500 error]</text>
    </g>
  </g>

  <!-- ========================================================================= -->
  <!-- USTUN 2: TELEGRAM BOT (X: 640, Width: 580)                                 -->
  <!-- ========================================================================= -->
  <g transform="translate(640, 120)">
    <rect x="0" y="0" width="580" height="1290" rx="14" fill="url(#col-bg)" stroke="#059669" stroke-width="1.8" filter="url(#shadow)"/>
    
    <!-- Title Badge -->
    <rect x="20" y="18" width="540" height="42" rx="8" fill="#064E3B" stroke="#10B981" stroke-width="1.2" />
    <text x="35" y="45" fill="#34D399" font-size="15" font-weight="800">🤖 2. TELEGRAM BOT (aiogram 3 Thin Client)</text>

    <!-- Node 2.1: Bosh menyu -->
    <g transform="translate(20, 75)">
      <rect x="0" y="0" width="540" height="240" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">📱 2.1 Bosh Menyu &amp; Reply Keyboard (/start)</text>

      <text x="25" y="52" fill="#34D399" font-size="11.5" font-weight="600">├── 🧭 Asosiy Reply Tugmalar:</text>
      <rect x="185" y="40" width="105" height="20" rx="4" fill="#065F46" /><text x="190" y="54" fill="#FFF" font-size="9.5">[🔍 Film qidirish]</text>
      <rect x="296" y="40" width="105" height="20" rx="4" fill="#065F46" /><text x="301" y="54" fill="#FFF" font-size="9.5">[🔥 Trend filmlar]</text>

      <text x="25" y="85" fill="#34D399" font-size="11.5" font-weight="600">├── 📂 Janrlar &amp; Katalog:</text>
      <rect x="165" y="73" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="87" fill="#CBD5E1" font-size="9.5">[📂 Janrlar]</text>
      <rect x="266" y="73" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="271" y="87" fill="#CBD5E1" font-size="9.5">[⭐ Sevimlilar]</text>
      <rect x="367" y="73" width="85" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="372" y="87" fill="#CBD5E1" font-size="9.5">[🕒 Tarix]</text>

      <text x="25" y="118" fill="#34D399" font-size="11.5" font-weight="600">├── 🌐 Veb-Portalga o'tish:</text>
      <rect x="165" y="106" width="135" height="20" rx="4" fill="#0284C7" /><text x="170" y="120" fill="#FFF" font-size="9.5">[🌐 WebApp ochish]</text>
      <rect x="306" y="106" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="311" y="120" fill="#CBD5E1" font-size="9.5">[🔗 Vebsayt havolasi]</text>

      <text x="25" y="151" fill="#34D399" font-size="11.5" font-weight="600">├── ⚙️ Bot Sozlamalari:</text>
      <rect x="165" y="139" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="153" fill="#CBD5E1" font-size="9.5">[⚙️ Sozlamalar]</text>
      <rect x="276" y="139" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="281" y="153" fill="#CBD5E1" font-size="9.5">[ℹ️ Bot haqida]</text>

      <text x="25" y="184" fill="#34D399" font-size="11.5" font-weight="600">└── 🚨 Yordam &amp; Aloqa:</text>
      <rect x="165" y="172" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="186" fill="#CBD5E1" font-size="9.5">[✍️ Film so'rash]</text>
      <rect x="286" y="172" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="291" y="186" fill="#CBD5E1" font-size="9.5">[📩 Adminga yozish]</text>
    </g>

    <!-- Node 2.2: Qidiruv & Inline Mode -->
    <g transform="translate(20, 330)">
      <rect x="0" y="0" width="540" height="260" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🔎 2.2 Qidiruv &amp; Inline Mode (@kinochi_bot)</text>

      <text x="25" y="52" fill="#34D399" font-size="11.5" font-weight="600">├── ⌨️ Matn orqali izlash:</text>
      <text x="165" y="52" fill="#CBD5E1" font-size="10.5">User nom kiritadi ➔ Inline natijalar ro'yxati</text>

      <text x="25" y="85" fill="#34D399" font-size="11.5" font-weight="600">├── 🔢 Film Kodi bo'yicha:</text>
      <text x="165" y="85" fill="#CBD5E1" font-size="10.5">Masalan "145" ➔ Filmni bevosita ekranga chiqarish</text>

      <text x="25" y="118" fill="#34D399" font-size="11.5" font-weight="600">├── ⚡ Inline Query rejimi:</text>
      <text x="175" y="118" fill="#CBD5E1" font-size="10.5">Har qanday chatda: @kinochi_bot &lt;nomi&gt; ➔ Snippet</text>

      <text x="25" y="151" fill="#34D399" font-size="11.5" font-weight="600">├── 📄 Inline Pagination:</text>
      <rect x="165" y="139" width="75" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="153" fill="#CBD5E1" font-size="9.5">[Btn: ◀️ Oldingi]</text>
      <rect x="246" y="139" width="75" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="251" y="153" fill="#CBD5E1" font-size="9.5">[Btn: Keyingi ▶️]</text>
      <rect x="327" y="139" width="85" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="332" y="153" fill="#CBD5E1" font-size="9.5">[Sahifa: 1/12]</text>

      <text x="25" y="184" fill="#34D399" font-size="11.5" font-weight="600">└── ❌ Topilmagan holat:</text>
      <rect x="165" y="172" width="135" height="20" rx="4" fill="#065F46" /><text x="170" y="186" fill="#34D399" font-size="9.5">[Btn: Film buyurtma berish]</text>
    </g>

    <!-- Node 2.3: Kontent kartochkasi & Inline Tugmalar -->
    <g transform="translate(20, 605)">
      <rect x="0" y="0" width="540" height="260" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🎬 2.3 Kontent Kartochkasi (Inline Buttons)</text>

      <text x="25" y="52" fill="#34D399" font-size="11.5" font-weight="600">├── 🎥 Tomosha qilish:</text>
      <rect x="155" y="40" width="135" height="20" rx="4" fill="#0284C7" /><text x="160" y="54" fill="#FFF" font-size="9.5">[Btn: ▶️ Vebsaytda ko'rish]</text>
      <rect x="296" y="40" width="125" height="20" rx="4" fill="#065F46" /><text x="301" y="54" fill="#FFF" font-size="9.5">[Btn: 📥 Faylni yuklash]</text>

      <text x="25" y="85" fill="#34D399" font-size="11.5" font-weight="600">├── 🎞️ Serial navigatsiyasi:</text>
      <rect x="165" y="73" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="87" fill="#CBD5E1" font-size="9.5">[Mavsum 1, 2...]</text>
      <rect x="266" y="73" width="75" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="271" y="87" fill="#CBD5E1" font-size="9.5">[1-qism]</text>
      <rect x="347" y="73" width="75" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="352" y="87" fill="#CBD5E1" font-size="9.5">[2-qism]</text>

      <text x="25" y="118" fill="#34D399" font-size="11.5" font-weight="600">├── ⭐ Shaxsiy harakatlar:</text>
      <rect x="175" y="106" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="180" y="120" fill="#F59E0B" font-size="9.5">[Btn: ⭐️ Sevimlilar]</text>
      <rect x="296" y="106" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="301" y="120" fill="#CBD5E1" font-size="9.5">[Btn: 🎬 Treyler]</text>

      <text x="25" y="151" fill="#34D399" font-size="11.5" font-weight="600">├── 👥 Do'stlarga ulashish:</text>
      <rect x="175" y="139" width="125" height="20" rx="4" fill="#0284C7" /><text x="180" y="153" fill="#FFF" font-size="9.5">[Btn: 👥 Do'stlarga ulashish]</text>

      <text x="25" y="184" fill="#34D399" font-size="11.5" font-weight="600">└── 🚨 Shikoyat tugmasi:</text>
      <rect x="165" y="172" width="115" height="20" rx="4" fill="#450A0A" /><text x="170" y="186" fill="#F87171" font-size="9.5">[Btn: ⚠️ Xabar berish]</text>
    </g>

    <!-- Node 2.4: FSM Holatlar & Shaxsiy bo'lim -->
    <g transform="translate(20, 880)">
      <rect x="0" y="0" width="540" height="210" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🔄 2.4 FSM So'rovlar &amp; Shaxsiy Bo'lim</text>

      <text x="25" y="52" fill="#34D399" font-size="11.5" font-weight="600">├── ✍️ Film so'rash FSM:</text>
      <rect x="165" y="40" width="125" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="54" fill="#CBD5E1" font-size="9.5">[FSM: Nomi kutilmoqda]</text>
      <rect x="296" y="40" width="75" height="20" rx="4" fill="#450A0A" /><text x="301" y="54" fill="#F87171" font-size="9.5">[Btn: ❌ Bekor]</text>

      <text x="25" y="85" fill="#34D399" font-size="11.5" font-weight="600">├── ⚠️ Shikoyat yuborish FSM:</text>
      <rect x="185" y="73" width="125" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="190" y="87" fill="#CBD5E1" font-size="9.5">[FSM: Matn kutilmoqda]</text>
      <rect x="316" y="73" width="75" height="20" rx="4" fill="#450A0A" /><text x="321" y="87" fill="#F87171" font-size="9.5">[Btn: ❌ Bekor]</text>

      <text x="25" y="118" fill="#34D399" font-size="11.5" font-weight="600">├── ⭐️ Sevimlilar ro'yxati:</text>
      <rect x="175" y="106" width="95" height="20" rx="4" fill="#450A0A" /><text x="180" y="120" fill="#F87171" font-size="9.5">[Btn: ❌ O'chirish]</text>
      <rect x="276" y="106" width="115" height="20" rx="4" fill="#450A0A" stroke="#DC2626" /><text x="281" y="120" fill="#F87171" font-size="9.5">[Btn: 🗑 Tozalash]</text>

      <text x="25" y="151" fill="#34D399" font-size="11.5" font-weight="600">└── 🕒 Tomosha tarixi:</text>
      <rect x="165" y="139" width="115" height="20" rx="4" fill="#0284C7" /><text x="170" y="153" fill="#FFF" font-size="9.5">[Btn: Qayta ko'rish]</text>
      <rect x="286" y="139" width="115" height="20" rx="4" fill="#450A0A" stroke="#DC2626" /><text x="291" y="153" fill="#F87171" font-size="9.5">[Btn: 🧹 Tozalash]</text>
    </g>

    <!-- Node 2.5: Admin Buyruqlari (Bot ichida) -->
    <g transform="translate(20, 1105)">
      <rect x="0" y="0" width="540" height="160" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🛡️ 2.5 Bot Ichidagi Maxsus Admin Buyruqlari</text>

      <text x="25" y="52" fill="#34D399" font-size="11.5" font-weight="600">├── 📊 /stats:</text>
      <text x="115" y="52" fill="#CBD5E1" font-size="10.5">Foydalanuvchilar soni, filmlar, ko'rishlar statistikasi</text>

      <text x="25" y="85" fill="#34D399" font-size="11.5" font-weight="600">├── 📢 /broadcast:</text>
      <text x="145" y="85" fill="#CBD5E1" font-size="10.5">Bot orqali tezkor e'lon yuborish oqimi</text>

      <text x="25" y="118" fill="#34D399" font-size="11.5" font-weight="600">└── ⚙️ /admin:</text>
      <text x="125" y="118" fill="#CBD5E1" font-size="10.5">Admin veb-paneliga bir martalik xavfsiz login havolasi</text>
    </g>
  </g>

  <!-- ========================================================================= -->
  <!-- USTUN 3: ADMIN PANEL (X: 1250, Width: 580)                                 -->
  <!-- ========================================================================= -->
  <g transform="translate(1250, 120)">
    <rect x="0" y="0" width="580" height="1290" rx="14" fill="url(#col-bg)" stroke="#E50914" stroke-width="1.8" filter="url(#shadow)"/>
    
    <!-- Title Badge -->
    <rect x="20" y="18" width="540" height="42" rx="8" fill="#450A0A" stroke="#EF4444" stroke-width="1.2" />
    <text x="35" y="45" fill="#F87171" font-size="15" font-weight="800">🛡️ 3. ADMIN PANEL (Next.js 14 Dashboard)</text>

    <!-- Node 3.1: Dashboard & Analitika -->
    <g transform="translate(20, 75)">
      <rect x="0" y="0" width="540" height="240" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">📊 3.1 Dashboard &amp; Statistika (/admin, /analytics)</text>

      <text x="25" y="52" fill="#F87171" font-size="11.5" font-weight="600">├── 📈 KPI Ko'rsatkichlari:</text>
      <rect x="175" y="40" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="180" y="54" fill="#38BDF8" font-size="9.5">[KPI: Jami Filmlar]</text>
      <rect x="276" y="40" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="281" y="54" fill="#34D399" font-size="9.5">[KPI: Seriallar]</text>
      <rect x="377" y="40" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="382" y="54" fill="#F59E0B" font-size="9.5">[KPI: Userlar]</text>

      <text x="25" y="85" fill="#F87171" font-size="11.5" font-weight="600">├── 📊 Diagramma va Grafika:</text>
      <text x="185" y="85" fill="#CBD5E1" font-size="10.5">Kunlik ko'rishlar grafigi, Scraper faollik tahlili</text>

      <text x="25" y="118" fill="#F87171" font-size="11.5" font-weight="600">├── ⚡ Tizim amallari:</text>
      <rect x="155" y="106" width="135" height="20" rx="4" fill="#450A0A" stroke="#DC2626" /><text x="160" y="120" fill="#F87171" font-size="9.5">[Btn: 🧹 Purge Redis Cache]</text>
      <rect x="296" y="106" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="301" y="120" fill="#CBD5E1" font-size="9.5">[Btn: 🔄 Yangilash]</text>

      <text x="25" y="151" fill="#F87171" font-size="11.5" font-weight="600">├── 🔐 Xavfsizlik &amp; Sessiya:</text>
      <rect x="175" y="139" width="105" height="20" rx="4" fill="#0284C7" /><text x="180" y="153" fill="#FFF" font-size="9.5">[Btn: Token yangilash]</text>
      <rect x="286" y="139" width="95" height="20" rx="4" fill="#450A0A" /><text x="291" y="153" fill="#F87171" font-size="9.5">[Btn: Logout]</text>

      <text x="25" y="184" fill="#F8F171" font-size="11.5" font-weight="600">└── ⚙️ Tizim holati (Health):</text>
      <rect x="185" y="172" width="85" height="20" rx="4" fill="#065F46" /><text x="190" y="186" fill="#34D399" font-size="9.5">[DB: OK]</text>
      <rect x="276" y="172" width="85" height="20" rx="4" fill="#065F46" /><text x="281" y="186" fill="#34D399" font-size="9.5">[Redis: OK]</text>
      <rect x="367" y="172" width="85" height="20" rx="4" fill="#065F46" /><text x="372" y="186" fill="#34D399" font-size="9.5">[Bot: OK]</text>
    </g>

    <!-- Node 3.2: Kontent Boshqaruvi -->
    <g transform="translate(20, 330)">
      <rect x="0" y="0" width="540" height="260" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🎬 3.2 Kontent Boshqaruvi (/admin/movies, /series)</text>

      <text x="25" y="52" fill="#F87171" font-size="11.5" font-weight="600">├── ➕ Yangi kontent qo'shish:</text>
      <rect x="185" y="40" width="115" height="20" rx="4" fill="#DC2626" /><text x="190" y="54" fill="#FFF" font-size="9.5">[Btn: + Yangi Film]</text>
      <rect x="306" y="40" width="115" height="20" rx="4" fill="#DC2626" /><text x="311" y="54" fill="#FFF" font-size="9.5">[Btn: + Yangi Serial]</text>

      <text x="25" y="85" fill="#F87171" font-size="11.5" font-weight="600">├── ✏️ Amallar &amp; Tahrirlash:</text>
      <rect x="175" y="73" width="75" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="180" y="87" fill="#CBD5E1" font-size="9.5">[Btn: Tahrir]</text>
      <rect x="256" y="73" width="75" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="261" y="87" fill="#CBD5E1" font-size="9.5">[Btn: Ko'rish]</text>
      <rect x="337" y="73" width="75" height="20" rx="4" fill="#450A0A" /><text x="342" y="87" fill="#F87171" font-size="9.5">[Btn: O'chirish]</text>

      <text x="25" y="118" fill="#F87171" font-size="11.5" font-weight="600">├── 🚀 Chop etish statusi:</text>
      <rect x="175" y="106" width="115" height="20" rx="4" fill="#059669" /><text x="180" y="120" fill="#FFF" font-size="9.5">[Btn: 🚀 Chop etish]</text>
      <rect x="296" y="106" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="301" y="120" fill="#CBD5E1" font-size="9.5">[Btn: ⏸ Draft]</text>

      <text x="25" y="151" fill="#F87171" font-size="11.5" font-weight="600">├── 📑 Serial qismlari &amp; File ID:</text>
      <rect x="195" y="139" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="200" y="153" fill="#CBD5E1" font-size="9.5">[Btn: + Mavsum]</text>
      <rect x="306" y="139" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="311" y="153" fill="#CBD5E1" font-size="9.5">[Btn: + Qism]</text>

      <text x="25" y="184" fill="#F87171" font-size="11.5" font-weight="600">└── 🔍 Filtrlash &amp; Qidiruv:</text>
      <rect x="175" y="172" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="180" y="186" fill="#34D399" font-size="9.5">[Status: All]</text>
      <rect x="276" y="172" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="281" y="186" fill="#F59E0B" font-size="9.5">[Status: Pending]</text>
    </g>

    <!-- Node 3.3: Avtopilot Scraper & Navbat -->
    <g transform="translate(20, 605)">
      <rect x="0" y="0" width="540" height="260" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🤖 3.3 Avtopilot Scraper &amp; Ingest Navbati (/autopilot)</text>

      <text x="25" y="52" fill="#F87171" font-size="11.5" font-weight="600">├── 🚀 Scraperni boshqarish:</text>
      <rect x="175" y="40" width="115" height="20" rx="4" fill="#059669" /><text x="180" y="54" fill="#FFF" font-size="9.5">[Btn: ▶️ Ishga tushir]</text>
      <rect x="296" y="40" width="105" height="20" rx="4" fill="#450A0A" /><text x="301" y="54" fill="#F87171" font-size="9.5">[Btn: ⏹ To'xtatish]</text>

      <text x="25" y="85" fill="#F87171" font-size="11.5" font-weight="600">├── 📥 Ingest navbati (/ingest):</text>
      <rect x="185" y="73" width="85" height="20" rx="4" fill="#059669" /><text x="190" y="87" fill="#FFF" font-size="9.5">[Btn: ✅ Qabul]</text>
      <rect x="276" y="73" width="75" height="20" rx="4" fill="#450A0A" /><text x="281" y="87" fill="#F87171" font-size="9.5">[Btn: ❌ Rad]</text>
      <rect x="357" y="73" width="95" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="362" y="87" fill="#CBD5E1" font-size="9.5">[Btn: 🔄 Retry]</text>

      <text x="25" y="118" fill="#F87171" font-size="11.5" font-weight="600">├── 🧹 Navbatni tozalash:</text>
      <rect x="175" y="106" width="135" height="20" rx="4" fill="#450A0A" stroke="#DC2626" /><text x="180" y="120" fill="#F87171" font-size="9.5">[Btn: 🗑 Navbatni tozalash]</text>

      <text x="25" y="151" fill="#F87171" font-size="11.5" font-weight="600">├── 🔌 Manba kalitlari:</text>
      <rect x="165" y="139" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="153" fill="#34D399" font-size="9.5">[Toggle: Uzmovi ON]</text>
      <rect x="286" y="139" width="125" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="291" y="153" fill="#34D399" font-size="9.5">[Toggle: Asilmedia ON]</text>

      <text x="25" y="184" fill="#F87171" font-size="11.5" font-weight="600">└── ⚙️ Avtomatik chop etish:</text>
      <rect x="185" y="172" width="155" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="190" y="186" fill="#F59E0B" font-size="9.5">[Toggle: Auto-publish OFF]</text>
    </g>

    <!-- Node 3.4: Foydalanuvchilar & Broadcast -->
    <g transform="translate(20, 880)">
      <rect x="0" y="0" width="540" height="210" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">👥 3.4 Foydalanuvchilar, Broadcast &amp; Moderatsiya</text>

      <text x="25" y="52" fill="#F87171" font-size="11.5" font-weight="600">├── 👤 User boshqaruvi (/users):</text>
      <rect x="185" y="40" width="105" height="20" rx="4" fill="#450A0A" /><text x="190" y="54" fill="#F87171" font-size="9.5">[Btn: 🚫 Ban qilish]</text>
      <rect x="296" y="40" width="105" height="20" rx="4" fill="#065F46" /><text x="301" y="54" fill="#34D399" font-size="9.5">[Btn: 🟢 Unban]</text>

      <text x="25" y="85" fill="#F87171" font-size="11.5" font-weight="600">├── 📢 Xabarnoma (/broadcast):</text>
      <rect x="195" y="73" width="105" height="20" rx="4" fill="#0284C7" /><text x="200" y="87" fill="#FFF" font-size="9.5">[Btn: 📲 Test jo'nat]</text>
      <rect x="306" y="73" width="115" height="20" rx="4" fill="#DC2626" /><text x="311" y="87" fill="#FFF" font-size="9.5">[Btn: 🚀 Hammaga yubor]</text>

      <text x="25" y="118" fill="#F87171" font-size="11.5" font-weight="600">├── 📩 Shikoyatlar (/reports):</text>
      <rect x="185" y="106" width="105" height="20" rx="4" fill="#059669" /><text x="190" y="120" fill="#FFF" font-size="9.5">[Btn: ✅ Hal etildi]</text>
      <rect x="296" y="106" width="95" height="20" rx="4" fill="#450A0A" /><text x="301" y="120" fill="#F87171" font-size="9.5">[Btn: ❌ Rad et]</text>

      <text x="25" y="151" fill="#F87171" font-size="11.5" font-weight="600">└── 📝 Buyurtmalar (/requests):</text>
      <rect x="185" y="139" width="105" height="20" rx="4" fill="#059669" /><text x="190" y="153" fill="#FFF" font-size="9.5">[Btn: 🎬 Bajarildi]</text>
      <rect x="296" y="139" width="105" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="301" y="153" fill="#CBD5E1" font-size="9.5">[Btn: 🔄 Qayta ko'r]</text>
    </g>

    <!-- Node 3.5: Audit loglar & Tizim -->
    <g transform="translate(20, 1105)">
      <rect x="0" y="0" width="540" height="160" rx="10" fill="url(#card-inner)" stroke="#1E293B" />
      <text x="15" y="25" fill="#F8FAFC" font-size="13.5" font-weight="700">🔒 3.5 Audit Loglar &amp; Ruxsatlar (/audit-logs)</text>

      <text x="25" y="52" fill="#F87171" font-size="11.5" font-weight="600">├── 📜 Audit xronologiyasi:</text>
      <text x="175" y="52" fill="#CBD5E1" font-size="10.5">Admin harakatlari (o'chirish, tahrirlash, login) logi</text>

      <text x="25" y="85" fill="#F87171" font-size="11.5" font-weight="600">├── 📥 Eksport qilish:</text>
      <rect x="165" y="73" width="115" height="20" rx="4" fill="#1E293B" stroke="#475569" /><text x="170" y="87" fill="#CBD5E1" font-size="9.5">[Btn: 📥 CSV Export]</text>

      <text x="25" y="118" fill="#F87171" font-size="11.5" font-weight="600">└── 👮 Rollar &amp; Ruxsatlar:</text>
      <text x="175" y="118" fill="#CBD5E1" font-size="10.5">Super Admin, Admin, Moderator darajalari</text>
    </g>
  </g>
</svg>
"""

# HTML Wrapper for direct in-browser inspection
html_content = f"""<!DOCTYPE html>
<html lang="uz">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Kinochi / MediaPlus — Barcha Funksiyalar va Tugmalar Daraxti</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: #040711;
      color: #E2E8F0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      padding: 20px;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .header-bar {{
      width: 100%;
      max-width: 1860px;
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #0E1626;
      border: 1px solid #1E293B;
      padding: 16px 24px;
      border-radius: 12px;
    }}
    .title {{ font-size: 18px; font-weight: 700; color: #FFF; }}
    .badge-group {{ display: flex; gap: 10px; }}
    .badge {{
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
    }}
    .badge-web {{ background: #082F49; color: #38BDF8; border: 1px solid #0284C7; }}
    .badge-bot {{ background: #064E3B; color: #34D399; border: 1px solid #059669; }}
    .badge-admin {{ background: #450A0A; color: #F87171; border: 1px solid #DC2626; }}
    .svg-container {{
      width: 100%;
      max-width: 1860px;
      background: #060913;
      border: 1px solid #1F2937;
      border-radius: 14px;
      overflow: auto;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4);
    }}
  </style>
</head>
<body>
  <div class="header-bar">
    <div class="title">🎬 Kinochi / MediaPlus — Ekotizim Funksiyalari Daraxti (Hierarchical Tree)</div>
    <div class="badge-group">
      <span class="badge badge-web">🌐 Websayt: 25 Sahifa</span>
      <span class="badge badge-bot">🤖 Telegram Bot: 7 Modul</span>
      <span class="badge badge-admin">🛡️ Admin Panel: 19 Bo'lim</span>
    </div>
  </div>
  <div class="svg-container">
    {svg_content}
  </div>
</body>
</html>
"""

os.makedirs("docs", exist_ok=True)

with open("docs/full_feature_tree.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

with open("docs/full_feature_tree.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Successfully generated: docs/full_feature_tree.svg ({len(svg_content)} chars)")
print(f"Successfully generated: docs/full_feature_tree.html ({len(html_content)} chars)")
