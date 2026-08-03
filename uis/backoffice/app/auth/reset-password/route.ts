import bcrypt from "bcryptjs";
import { NextResponse } from "next/server";
import { consumeResetToken, findUserById, updateUserPassword } from "@/lib/authStore";
import { verifyPasswordResetToken } from "@/lib/passwordReset";

type ResetPasswordBody = {
  token?: unknown;
  new_password?: unknown;
};

function isValidPassword(value: string): boolean {
  return value.length >= 8;
}

export async function POST(request: Request) {
  let token = "";
  let newPassword = "";

  try {
    const body = (await request.json()) as ResetPasswordBody;
    token = typeof body.token === "string" ? body.token.trim() : "";
    newPassword = typeof body.new_password === "string" ? body.new_password : "";
  } catch {
    return NextResponse.json({ error: "Invalid or expired token" }, { status: 400 });
  }

  if (!token || !isValidPassword(newPassword)) {
    return NextResponse.json({ error: "Invalid or expired token" }, { status: 400 });
  }

  const verified = await verifyPasswordResetToken(token);

  if (!verified) {
    return NextResponse.json({ error: "Invalid or expired token" }, { status: 400 });
  }

  const user = await findUserById(verified.userId);

  if (!user) {
    return NextResponse.json({ error: "Invalid or expired token" }, { status: 400 });
  }

  const consumed = await consumeResetToken(verified.jti, verified.userId);
  if (!consumed) {
    return NextResponse.json({ error: "Invalid or expired token" }, { status: 400 });
  }

  const passwordHash = await bcrypt.hash(newPassword, 12);
  const didUpdate = await updateUserPassword(user.id, passwordHash);

  if (!didUpdate) {
    return NextResponse.json({ error: "Unable to reset password" }, { status: 500 });
  }

  return NextResponse.json({ message: "Password reset successful" }, { status: 200 });
}