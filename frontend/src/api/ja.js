import { apiFetch } from "./client";

const BASE = "/api/v1/therapy/games/ja";

/**
 * Backend returns:
 * {
 *   session: { session_id, trials_planned, time_limit_ms },
 *   first_trial: { trial_id, prompt, options, ... } OR { detail, summary? },
 *   summary?: {...}
 * }
 */
export function startSession(
  child_id,
  trials_planned = 10,
  {
    time_limit_ms = 10000,
    supervision_mode = "therapist",
    session_title = null,
  } = {}
) {
  const body = {
    child_id,
    trials_planned,
    time_limit_ms,
    supervision_mode,
  };
  if (session_title) body.session_title = session_title;

  return apiFetch(`${BASE}/start/`, { method: "POST", body });
}

export function nextTrial(session_id) {
  return apiFetch(`${BASE}/${session_id}/next/`, { method: "POST", body: {} });
}

/**
 * IMPORTANT:
 * Backend expects: clicked (NOT clicked_id)
 */
export function submitTrial(trial_id, clicked, response_time_ms, timed_out) {
  return apiFetch(`${BASE}/trial/${trial_id}/submit/`, {
    method: "POST",
    body: { clicked, response_time_ms, timed_out },
  });
}

export function summary(session_id) {
  return apiFetch(`${BASE}/${session_id}/summary/`, { method: "GET" });
}
