"use client";

import { FormEvent, useState } from "react";
import {
  flushNow,
  setTelemetryIdentity,
  track,
  timedFetch,
} from "@/src/services/telemetry";

const API =
  process.env.NEXT_PUBLIC_OPERATIONS_API_URL || "http://127.0.0.1:8005";

export default function LoginPage() {
  const [username, setUsername] = useState("ana");
  const [password, setPassword] = useState("trackflow");
  const [message, setMessage] = useState("");

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const res = await timedFetch(`${API}/inventory/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!data.ok) {
      track("user_login_failed", { failure_code: data.failure_code || "unknown" });
      await flushNow();
      setMessage(`Login failed: ${data.failure_code}`);
      return;
    }
    setTelemetryIdentity(data.userId, data.sessionId);
    track("user_login_succeeded", { method: "password" });
    await flushNow();
    setMessage(`Logged in as ${data.userId}`);
  }

  return (
    <main className="mx-auto max-w-md px-6 py-10">
      <h1 className="text-2xl font-semibold">Operator login</h1>
      <p className="mt-2 text-sm text-slate-400">
        Demo password: <code>trackflow</code>
      </p>
      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <label className="block text-sm">
          Username
          <input
            className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          Password
          <input
            type="password"
            className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button
          type="submit"
          className="rounded bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500"
        >
          Sign in
        </button>
      </form>
      {message && <p className="mt-4 text-sm text-slate-300">{message}</p>}
    </main>
  );
}
