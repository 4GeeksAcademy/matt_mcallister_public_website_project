import { Resend } from "resend";

function getAppBaseUrl(): string {
  return process.env.APP_BASE_URL?.trim() || "http://localhost:3000";
}

function getResendClient(): Resend {
  const apiKey = process.env.RESEND_API_KEY?.trim();
  if (!apiKey) {
    throw new Error("RESEND_API_KEY is required to send password reset emails");
  }

  return new Resend(apiKey);
}

export async function sendPasswordResetEmail(email: string, token: string): Promise<void> {
  const resetLink = `${getAppBaseUrl()}/reset-password?token=${encodeURIComponent(token)}`;
  const resend = getResendClient();

  const response = await resend.emails.send({
    from: process.env.RESEND_FROM_EMAIL?.trim() || "onboarding@resend.dev",
    to: email,
    subject: "Reset your TrackFlow password",
    html: `
      <div style="font-family:Arial,sans-serif;line-height:1.6;color:#111827;padding:16px;max-width:600px;margin:0 auto;">
        <h1 style="font-size:20px;margin:0 0 12px;">Reset your password</h1>
        <p style="margin:0 0 12px;">We received a request to reset your password. Tap the button below to continue.</p>
        <p style="margin:20px 0;">
          <a href="${resetLink}" style="display:inline-block;background:#0f172a;color:#ffffff;text-decoration:none;padding:12px 18px;border-radius:8px;font-weight:600;">Reset password</a>
        </p>
        <p style="margin:0 0 8px;word-break:break-all;">If the button does not work, copy this link into your browser:</p>
        <p style="margin:0;color:#1d4ed8;word-break:break-all;">${resetLink}</p>
        <p style="margin:16px 0 0;color:#6b7280;font-size:14px;">If you did not request this, you can safely ignore this email.</p>
      </div>
    `,
    text: `Reset your TrackFlow password\n\nOpen this link: ${resetLink}\n\nIf you did not request this, you can ignore this email.`,
  });

  if (response.error) {
    throw new Error(`Resend failed to send password reset email: ${response.error.message}`);
  }
}