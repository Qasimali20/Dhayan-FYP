import { apiFetch } from "./client";

const BASE = "/api/v1/speech";

// ── Activities ──

export function getSpeechActivities(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`${BASE}/activities${qs ? "?" + qs : ""}`);
}

export function getSpeechActivity(activityId) {
  return apiFetch(`${BASE}/activities/${activityId}`);
}

export function createSpeechActivity(data) {
  return apiFetch(`${BASE}/activities`, { method: "POST", body: data });
}

// ── Sessions ──

export function startSpeechSession({ child_id, activity_id, trials_planned = 8, supervision_mode = "therapist", prompt_level = 0 }) {
  return apiFetch(`${BASE}/sessions/start`, {
    method: "POST",
    body: { child_id, activity_id, trials_planned, supervision_mode, prompt_level },
  });
}

export function getSpeechSessionSummary(sessionId) {
  return apiFetch(`${BASE}/sessions/${sessionId}/summary`);
}

// ── Trials ──

export function uploadSpeechAudio(trialId, file, durationMs) {
  const formData = new FormData();
  formData.append("file", file);
  if (durationMs) formData.append("duration_ms", durationMs);

  return apiFetch(`${BASE}/trials/${trialId}/upload-audio`, {
    method: "POST",
    rawBody: formData,   // don't JSON.stringify
    headers: {},          // let browser set content-type with boundary
  });
}

export function getSpeechAnalysis(trialId) {
  return apiFetch(`${BASE}/trials/${trialId}/analysis`);
}

export function scoreSpeechTrial(trialId, { score, notes = "", override_transcript = "" }) {
  return apiFetch(`${BASE}/trials/${trialId}/score`, {
    method: "POST",
    body: { score, notes, override_transcript },
  });
}

// ── Progress ──

export function getSpeechProgress(childProfileId) {
  return apiFetch(`${BASE}/children/${childProfileId}/progress`);
}
