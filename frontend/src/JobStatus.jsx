import { useEffect, useState } from "react";
import { getJob, resultUrl } from "./api";

const STATUS_LABELS = {
  queued: "Queued",
  processing: "Processing",
  completed: "Completed",
  failed: "Failed",
  dead_letter: "Dead-lettered",
};

export default function JobStatus({ job, onUpdate }) {
  const [current, setCurrent] = useState(job);

  useEffect(() => {
    setCurrent(job);

    // Terminal states never change again — no point polling them.
    if (["completed", "failed", "dead_letter"].includes(job.status)) {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await getJob(job.id);
        setCurrent(updated);
        onUpdate(updated);
        if (["completed", "failed", "dead_letter"].includes(updated.status)) {
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [job.id, job.status]);

  return (
    <div className={`job-card status-${current.status}`}>
      <div className="job-card-header">
        <span className="job-id">{current.id.slice(0, 8)}</span>
        <span className={`lane-badge lane-${current.priority}`}>
          {current.priority} lane
        </span>
      </div>
      <p className="job-status-label">{STATUS_LABELS[current.status]}</p>
      {current.retry_count > 0 && (
        <p className="job-meta">Retried {current.retry_count} time(s)</p>
      )}
      {current.error_message && (
        <p className="job-error">{current.error_message}</p>
      )}
      {current.status === "completed" && (
        <a className="result-link" href={resultUrl(current.id)} download>
          Download result
        </a>
      )}
    </div>
  );
}