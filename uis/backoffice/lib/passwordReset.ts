import crypto from "node:crypto";
import jwt from "jsonwebtoken";
import { isResetTokenActive, saveResetToken } from "@/lib/authStore";

type PasswordResetClaims = {
  sub: string;
  jti: string;
  purpose: "password_reset";
};

type VerifiedPasswordResetToken = {
  userId: string;
  jti: string;
};

function getJwtSecret(): string {
  const secret = process.env.RESET_TOKEN_SECRET;
  if (!secret) {
    throw new Error("RESET_TOKEN_SECRET is required");
  }

  return secret;
}

function getResetExpiryMinutes(): number {
  const raw = Number(process.env.RESET_TOKEN_EXPIRY_MINUTES || "30");
  if (!Number.isFinite(raw)) {
    return 30;
  }

  return Math.max(15, Math.min(60, Math.floor(raw)));
}

export async function createPasswordResetToken(userId: string): Promise<string> {
  const secret = getJwtSecret();
  const jti = crypto.randomUUID();
  const expiresInMinutes = getResetExpiryMinutes();
  const expiresAt = Date.now() + expiresInMinutes * 60 * 1000;

  const claims: PasswordResetClaims = {
    sub: userId,
    jti,
    purpose: "password_reset",
  };

  const token = jwt.sign(claims, secret, {
    expiresIn: `${expiresInMinutes}m`,
  });

  await saveResetToken(jti, userId, expiresAt);

  return token;
}

export async function verifyPasswordResetToken(token: string): Promise<VerifiedPasswordResetToken | null> {
  try {
    const payload = jwt.verify(token, getJwtSecret());

    if (!payload || typeof payload !== "object") {
      return null;
    }

    const userId = typeof payload.sub === "string" ? payload.sub : null;
    const jti = typeof payload.jti === "string" ? payload.jti : null;
    const purpose = payload.purpose;

    if (!userId || !jti || purpose !== "password_reset") {
      return null;
    }

    if (!(await isResetTokenActive(jti, userId))) {
      return null;
    }

    return {
      userId,
      jti,
    };
  } catch {
    return null;
  }
}