const BASE_URL = "http://localhost:8000";

export async function createJob(file, priority) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("priority", priority);

  const res = await fetch(`${BASE_URL}/jobs`, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function getJob(jobId) {
  const res = await fetch(`${BASE_URL}/jobs/${jobId}`);
  if (!res.ok) throw new Error("Job not found");
  return res.json();
}

export async function listDeadLetterJobs() {
  const res = await fetch(`${BASE_URL}/admin/dead-letter`);
  if (!res.ok) throw new Error("Could not load dead-letter jobs");
  return res.json();
}

export async function retryDeadLetterJob(jobId) {
  const res = await fetch(`${BASE_URL}/admin/dead-letter/${jobId}/retry`, { method: "POST" });
  if (!res.ok) throw new Error("Retry failed");
  return res.json();
}

export function resultUrl(jobId) {
  return `${BASE_URL}/jobs/${jobId}/result`;
}