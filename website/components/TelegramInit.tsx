"use client";

import { useEffect } from "react";
import { initTelegram } from "@/lib/telegram";

export default function TelegramInit() {
  useEffect(() => {
    initTelegram();
  }, []);

  return null;
}