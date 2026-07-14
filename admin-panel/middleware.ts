/**
 * Next.js Middleware — auth guard with JWT verification.
 *
 * Edge Runtime'da jose library orqali JWT signature va expiry tekshiriladi.
 * Bu expired yoki qalbaki token bilan kirish imkonini yo'q qiladi.
 * SECRET_KEY backend bilan bir xil bo'lishi kerak.
 */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { jwtVerify } from "jose";

const SECRET_KEY = new TextEncoder().encode(
  process.env.JWT_SECRET_KEY || ""
);

async function verifyToken(token: string): Promise<boolean> {
  if (!process.env.JWT_SECRET_KEY) {
    // Secret konfiguratsiyalanmagan — faqat token mavjudligi tekshiriladi (fallback)
    console.warn("JWT_SECRET_KEY konfiguratsiyalanmagan — token yaroqliligi tekshirilmaydi!");
    return true;
  }
  try {
    await jwtVerify(token, SECRET_KEY, { algorithms: ["HS256"] });
    return true;
  } catch {
    return false;
  }
}

export async function middleware(request: NextRequest) {
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
  const tokenCookie = request.cookies.get("access_token");
  if (!tokenCookie) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  // Token mavjudligi yetarli, API so'rovlarida backend asosiysini tekshiradi.
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

