"use client";

import { FormEvent, useEffect, useState } from "react";

import { ApiError, userApi } from "@/lib/api-client";

type PasswordFields = {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
};

export default function ChangePasswordPage() {
  const [userId, setUserId] = useState<string | null>(null);
  const [fields, setFields] = useState<PasswordFields>({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [apiMessage, setApiMessage] = useState<string | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const loadUser = async () => {
      try {
        const me = await userApi.getMe();
        setUserId(me.id);
      } catch (error) {
        const fallback = "Unable to load account context for password update.";
        setApiError(error instanceof ApiError ? error.message || fallback : fallback);
      } finally {
        setIsLoadingUser(false);
      }
    };

    void loadUser();
  }, []);

  const setField = (key: keyof PasswordFields, value: string) => {
    setFields((prev) => ({ ...prev, [key]: value }));
    setFieldError(null);
    setApiError(null);
    setApiMessage(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!userId) {
      setApiError("No user context available. Please refresh and try again.");
      return;
    }

    if (fields.newPassword !== fields.confirmPassword) {
      setFieldError("New password and confirmation must match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await userApi.changePassword(userId, fields.currentPassword, fields.newPassword);
      setApiMessage("Password updated successfully.");
      setFields({ currentPassword: "", newPassword: "", confirmPassword: "" });
    } catch (error) {
      const fallback = "Unable to update password. Please try again.";
      setApiError(error instanceof ApiError ? error.message || fallback : fallback);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-10 md:px-10">
      <h1 className="text-2xl font-semibold">Change Password</h1>
      <p className="mt-2 text-sm text-slate-300">
        Update your password. You must confirm the new password before submitting.
      </p>

      <form className="mt-6 space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-5" onSubmit={handleSubmit}>
        <div>
          <label className="mb-1 block text-sm" htmlFor="currentPassword">
            Current password
          </label>
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
            id="currentPassword"
            onChange={(event) => setField("currentPassword", event.target.value)}
            required
            type="password"
            value={fields.currentPassword}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm" htmlFor="newPassword">
            New password
          </label>
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
            id="newPassword"
            onChange={(event) => setField("newPassword", event.target.value)}
            required
            type="password"
            value={fields.newPassword}
          />
        </div>

        <div>
          <label className="mb-1 block text-sm" htmlFor="confirmPassword">
            Confirm new password
          </label>
          <input
            className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
            id="confirmPassword"
            onChange={(event) => setField("confirmPassword", event.target.value)}
            required
            type="password"
            value={fields.confirmPassword}
          />
        </div>

        {fieldError ? (
          <p className="rounded-md border border-amber-700 bg-amber-900/30 px-3 py-2 text-sm text-amber-200">
            {fieldError}
          </p>
        ) : null}

        {apiMessage ? (
          <p className="rounded-md border border-green-700 bg-green-900/30 px-3 py-2 text-sm text-green-200">
            {apiMessage}
          </p>
        ) : null}

        {apiError ? (
          <p className="rounded-md border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-200">
            {apiError}
          </p>
        ) : null}

        <button
          className="rounded-md bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-70"
          disabled={isSubmitting || isLoadingUser}
          type="submit"
        >
          {isSubmitting ? "Updating..." : "Update password"}
        </button>
      </form>
    </div>
  );
}
