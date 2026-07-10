/**
 * Next.js Middleware — client-side auth guard.
 *
 * MVP qaror: access_token muddati tugasa, foydalanuvchi qayta login
 * qiladi. Avtomatik refresh middleware darajasida QILINMAYDI, chunki:
 *   1. Middleware Edge Runtime'da ishlaydi — backend'ga so'rov yuborish
 *      murakkab va ishonchsiz.
 *   2. MVP uchun oddiylik muhimroq; haqiqiy himoya backend'dagi
 *      get_current_admin orqali ta'minlanadi.
 *   3. Kelajakda fetchApi wrapper ichiga 401 → auto-refresh → retry
 *      logikasi qo'shilishi mumkin (client-side, middleware emas).
 */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Login sahifasini himoyalamaydi
  if (pathname.startsWith("/login")) {
    return NextResponse.next();
  }

  // _next static fayllarini o'tkazib yuborish
  if (pathname.startsWith("/_next") || pathname.startsWith("/favicon")) {
    return NextResponse.next();
  }

  // access_token cookie borligini tekshirish
  const token = request.cookies.get("access_token");
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
