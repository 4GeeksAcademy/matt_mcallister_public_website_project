"use client";

import { FormEvent, useEffect, useState } from "react";

import { ApiError, userApi } from "@/lib/api-client";

type UserProfile = {
  id: string;
  name: string;
  email: string;
};

export default function AccountProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [name, setName] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const me = await userApi.getMe();
        setProfile(me);
        setName(me.name);
      } catch (err) {
        const fallback = "Unable to load your profile right now.";
        setError(err instanceof ApiError ? err.message || fallback : fallback);
      } finally {
        setIsLoading(false);
      }
    };

    void loadProfile();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!profile) {
      return;
    }

    setError(null);
    setMessage(null);
    setIsSaving(true);

    try {
      await userApi.updateName(profile.id, name.trim());
      setProfile((prev) => (prev ? { ...prev, name: name.trim() } : prev));
      setMessage("Profile updated successfully.");
    } catch (err) {
      const fallback = "Unable to save profile changes.";
      setError(err instanceof ApiError ? err.message || fallback : fallback);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <div className="mx-auto w-full max-w-3xl px-6 py-10 md:px-10">Loading profile...</div>;
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-10 md:px-10">
      <h1 className="text-2xl font-semibold">Account Profile</h1>
      <p className="mt-2 text-sm text-slate-300">Edit your account details and keep your profile current.</p>

      <form className="mt-6 space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-5" onSubmit={handleSubmit}>
        <div>
          <label className="mb-1 block text-sm" htmlFor="email">
            Email
          </label>
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-400"
            id="email"
            readOnly
            value={profile?.email ?? ""}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm" htmlFor="name">
            Name
          </label>
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
            id="name"
            onChange={(event) => setName(event.target.value)}
            required
            value={name}
          />
        </div>

        {message ? (
          <p className="rounded-md border border-green-700 bg-green-900/30 px-3 py-2 text-sm text-green-200">
            {message}
          </p>
        ) : null}

        {error ? (
          <p className="rounded-md border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-200">
            {error}
          </p>
        ) : null}

        <button
          className="rounded-md bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-70"
          disabled={isSaving}
          type="submit"
        >
          {isSaving ? "Saving..." : "Save name"}
        </button>
      </form>
    </div>
  );
}
