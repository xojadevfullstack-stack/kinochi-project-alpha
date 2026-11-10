import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
      <h1 className="text-6xl font-black text-primary-container mb-4">404</h1>
      <h2 className="text-xl font-bold text-text-primary mb-2">Sahifa topilmadi</h2>
      <p className="text-sm text-zinc-400 mb-6">
        Siz qidirayotgan sahifa mavjud emas yoki boshqa manzilga ko'chirilgan.
      </p>
      <Link
        href="/"
        className="px-4 py-2 bg-primary-container hover:bg-primary-container/80 text-white rounded-xl text-sm font-semibold transition-all"
      >
        Bosh sahifaga qaytish
      </Link>
    </div>
  );
}
