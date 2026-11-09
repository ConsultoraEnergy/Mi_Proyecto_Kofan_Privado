import apiClient from "@/api/apiClient";

/** Inicia sesión. El backend deja el refresh token en una cookie HttpOnly. */
export async function login(email, password) {
  const body = new URLSearchParams({ username: email.trim(), password });
  const { data } = await apiClient.post("/auth/login", body);
  return data; // { access_token, token_type, expires_in, user }
}

export async function refresh() {
  const { data } = await apiClient.post("/auth/refresh");
  return data;
}

export const logout = () => apiClient.post("/auth/logout");
export const register = (payload) => apiClient.post("/auth/register", payload).then((r) => r.data);
export const verifyEmail = (token) => apiClient.post("/auth/verify-email", { token }).then((r) => r.data);
export const resendVerification = () => apiClient.post("/auth/resend-verification").then((r) => r.data);
export const forgotPassword = (email) => apiClient.post("/auth/forgot-password", { email }).then((r) => r.data);
export const resetPassword = (token, password) =>
  apiClient.post("/auth/reset-password", { token, password }).then((r) => r.data);
