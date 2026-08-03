"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { ApiError, authApi } from "@/lib/api-client";
import { hasValidSession, setToken } from "@/lib/auth";

type RegisterFields = {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
};

export default function RegisterPage() {
  const router = useRouter();
  const [fields, setFields] = useState<RegisterFields>({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof RegisterFields, string>>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (hasValidSession()) {
      router.replace("/");
    }
  }, [router]);

  const setField = <K extends keyof RegisterFields>(key: K, value: RegisterFields[K]) => {
    setFields((prev) => ({ ...prev, [key]: value }));
    setFieldErrors((prev) => ({ ...prev, [key]: undefined }));
    setGeneralError(null);
  };

  const validateClient = () => {
    const nextErrors: Partial<Record<keyof RegisterFields, string>> = {};

    if (fields.name.trim().length < 2) {
      nextErrors.name = "Name must contain at least 2 characters.";
    }

    if (fields.password.length < 8) {
      nextErrors.password = "Password must contain at least 8 characters.";
    }

    if (fields.password !== fields.confirmPassword) {
      nextErrors.confirmPassword = "Password confirmation does not match.";
    }

    setFieldErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const mapApiFieldErrors = (errors?: Record<string, string>) => {
    if (!errors) {
      return;
    }

    const nextErrors: Partial<Record<keyof RegisterFields, string>> = {};

    Object.entries(errors).forEach(([key, value]) => {
      if (key === "name" || key === "email" || key === "password" || key === "confirmPassword") {
        nextErrors[key] = value;
      }
    });

    setFieldErrors((prev) => ({ ...prev, ...nextErrors }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!validateClient()) {
      return;
    }

    setGeneralError(null);
    setIsSubmitting(true);

    try {
      const response = await authApi.register(fields.name, fields.email, fields.password);
      setToken(response.token);
      router.replace("/");
    } catch (error) {
      const fallback = "Registration failed. Please review your information and try again.";

      if (error instanceof ApiError) {
        mapApiFieldErrors(error.fieldErrors);
        setGeneralError(error.message || fallback);
      } else {
        setGeneralError(fallback);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-10 text-slate-100">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">TrackFlow</p>
        <h1 className="mt-2 text-2xl font-semibold">Create account</h1>
        <p className="mt-1 text-sm text-slate-400">Register to start using protected backoffice views.</p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 block text-sm" htmlFor="name">
              Name
            </label>
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
              id="name"
              onChange={(event) => setField("name", event.target.value)}
              required
              value={fields.name}
            />
            {fieldErrors.name ? <p className="mt-1 text-xs text-red-300">{fieldErrors.name}</p> : null}
          </div>

          <div>
            <label className="mb-1 block text-sm" htmlFor="email">
              Email
            </label>
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
              id="email"
              onChange={(event) => setField("email", event.target.value)}
              required
              type="email"
              value={fields.email}
            />
            {fieldErrors.email ? <p className="mt-1 text-xs text-red-300">{fieldErrors.email}</p> : null}
          </div>

          <div>
            <label className="mb-1 block text-sm" htmlFor="password">
              Password
            </label>
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
              id="password"
              onChange={(event) => setField("password", event.target.value)}
              required
              type="password"
              value={fields.password}
            />
            {fieldErrors.password ? <p className="mt-1 text-xs text-red-300">{fieldErrors.password}</p> : null}
          </div>

          <div>
            <label className="mb-1 block text-sm" htmlFor="confirmPassword">
              Confirm password
            </label>
            <input
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-cyan-400"
              id="confirmPassword"
              onChange={(event) => setField("confirmPassword", event.target.value)}
              required
              type="password"
              value={fields.confirmPassword}
            />
            {fieldErrors.confirmPassword ? (
              <p className="mt-1 text-xs text-red-300">{fieldErrors.confirmPassword}</p>
            ) : null}
          </div>

          {generalError ? (
            <p className="rounded-md border border-red-700 bg-red-900/30 px-3 py-2 text-sm text-red-200">
              {generalError}
            </p>
          ) : null}

          <button
            className="w-full rounded-md bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-70"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Creating account..." : "Register"}
          </button>
        </form>

        <p className="mt-4 text-sm text-slate-400">
          Already have an account?{" "}
          <Link className="text-cyan-300 hover:text-cyan-200" href="/login">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
