import { apiFetch } from "./client";

const BASE = "/api/v1/patients";

export function listChildren() {
  return apiFetch(`${BASE}/children`, { method: "GET" });
}

export function createChild({ email, full_name, date_of_birth, gender, diagnosis_notes }) {
  const body = { email, full_name };
  if (date_of_birth) body.date_of_birth = date_of_birth;
  if (gender) body.gender = gender;
  if (diagnosis_notes) body.diagnosis_notes = diagnosis_notes;
  return apiFetch(`${BASE}/children`, { method: "POST", body });
}
