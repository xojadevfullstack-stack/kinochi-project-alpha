"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getToken = getToken;
exports.setToken = setToken;
exports.clearToken = clearToken;
var TOKEN_KEY = "kinochi_jwt";
function getToken() {
    if (typeof window === "undefined") {
        return null;
    }
    return localStorage.getItem(TOKEN_KEY);
}
function setToken(token) {
    if (typeof window === "undefined") {
        return;
    }
    localStorage.setItem(TOKEN_KEY, token);
}
function clearToken() {
    if (typeof window === "undefined") {
        return;
    }
    localStorage.removeItem(TOKEN_KEY);
}
