"use client";

import Link from 'next/link';
import { useRouter } from 'next/navigation';

const API_URL = "/api/v1";

export default function Sidebar() {
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {
      // Even if request fails, redirect to login
    }
    router.push("/login");
  };

  return (
    <div className="w-64 bg-white h-screen shadow-md flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-gray-800">Kinochi Admin</h1>
      </div>
      <nav className="flex-1 px-4 space-y-2">
        <Link href="/" className="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md">
          Dashboard
        </Link>
        <Link href="/movies" className="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md">
          Movies
        </Link>
        <Link href="/series" className="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md">
          Series
        </Link>
        <Link href="/categories" className="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md">
          Categories
        </Link>
        <Link href="/channels" className="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md">
          Channels
        </Link>
        <Link href="/broadcasts" className="block px-4 py-2 text-gray-700 hover:bg-blue-50 hover:text-blue-600 rounded-md">
          Broadcasts
        </Link>
        <div className="block px-4 py-2 text-gray-400 cursor-not-allowed">
          Statistics (Coming soon)
        </div>
      </nav>
      <div className="p-4 border-t">
        <button
          onClick={handleLogout}
          className="w-full px-4 py-2 text-red-600 hover:bg-red-50 rounded-md text-sm font-medium transition"
        >
          🚪 Chiqish (Logout)
        </button>
      </div>
    </div>
  );
}
