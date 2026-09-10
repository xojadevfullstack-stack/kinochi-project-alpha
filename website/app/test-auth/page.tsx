"use client";
import { useAuth } from "../../lib/auth/AuthProvider";

export default function TestAuthPage() {
  const { status, user, token, environment } = useAuth();
  
  return (
    <div className="p-8">
      <h1 className="text-xl mb-4">Auth Status Test Page</h1>
      <p id="auth-status">Status: {status}</p>
      <p id="auth-env">Environment: {environment}</p>
      <p id="auth-token">Token: {token || "null"}</p>
      <p id="auth-user">User: {user ? user.first_name : "null"}</p>
    </div>
  );
}
