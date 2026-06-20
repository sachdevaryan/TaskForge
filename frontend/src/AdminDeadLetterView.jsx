import { useEffect, useState } from "react";
import { listDeadLetterJobs, retryDeadLetterJob } from "./api";

export default function AdminDeadLetterView() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    try {
      setJobs(await listDeadLetterJobs());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleRetry(jobId) {
    await retryDeadLetterJob(jobId);
    refresh();
  }

  if (loading) return <p>Loading dead-letter queue…</p>;

  return (
    <div className="admin-view">
      <h2>Dead-letter queue</h2>
      {jobs.length === 0 ? (
        <p className="empty-state">Nothing here — every job has either completed or is still in flight.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Job</th>
              <th>Priority</th>
              <th>Retries</th>
              <th>Error</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.id}>
                <td>{job.id.slice(0, 8)}</td>
                <td>{job.priority}</td>
                <td>{job.retry_count}</td>
                <td className="job-error-cell">{job.error_message}</td>
                <td>
                  <button onClick={() => handleRetry(job.id)}>Retry job</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}