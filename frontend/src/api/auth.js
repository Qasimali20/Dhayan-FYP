import { apiFetch, setToken, setRefreshToken, clearToken } from "./client";

export async function login(email, password) {
  const data = await apiFetch("/api/v1/auth/login", {
    method: "POST",
    body: { email, password },
    auth: false,
  });

  // simplejwt returns { access, refresh }
  if (data?.access) setToken(data.access);
  if (data?.refresh) setRefreshToken(data.refresh);

  return data;
}

export function logout() {
  clearToken();
}

// ── Signup ──

export async function signup({ email, full_name, phone, password, password2, role }) {
  return apiFetch("/api/v1/auth/signup", {
    method: "POST",
    body: { email, full_name, phone, password, password2, role },
    auth: false,
  });
}

// ── Forgot / Reset Password ──

export async function forgotPassword(email) {
  return apiFetch("/api/v1/auth/forgot-password", {
    method: "POST",
    body: { email },
    auth: false,
  });
}

export async function verifyOtp(email, otp) {
  return apiFetch("/api/v1/auth/verify-otp", {
    method: "POST",
    body: { email, otp },
    auth: false,
  });
}

export async function resetPassword(email, otp, new_password, new_password2) {
  return apiFetch("/api/v1/auth/reset-password", {
    method: "POST",
    body: { email, otp, new_password, new_password2 },
    auth: false,
  });
}

// ── Profile Update ──

export async function updateProfile({ full_name, phone }) {
  return apiFetch("/api/v1/auth/me", {
    method: "PATCH",
    body: { full_name, phone },
  });
}
