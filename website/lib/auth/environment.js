"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.detectEnvironment = detectEnvironment;
function detectEnvironment() {
    if (typeof window === "undefined") {
        // Should not be called during SSR, fallback to browser
        return "browser";
    }
    // Check if Telegram WebApp initData is present and non-empty
    if (window.Telegram &&
        window.Telegram.WebApp &&
        window.Telegram.WebApp.initData &&
        window.Telegram.WebApp.initData.trim() !== "") {
        return "telegram_webapp";
    }
    return "browser";
}
