import { useState } from "react";
import UploadForm from "./UploadForm";
import JobStatus from "./JobStatus";
import AdminDeadLetterView from "./AdminDeadLetterView";
import "./index.css";

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [view, setView] = useState("dashboard");

  function handleJobCreated(job) {
    setJobs((prev) => [job, ...prev]);
  }

  function handleJobUpdate(updated) {
    setJobs((prev) => prev.map((j) => (j.id === updated.id ? updated : j)));
  }

  const highLane = jobs.filter((j) => j.priority === "high");
  const lowLane = jobs.filter((j) => j.priority === "low");

  return (
    <div className="app">
      <header>
        <h1>TaskForge</h1>
        <nav>
          <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}>
            Dashboard
          </button>
          <button className={view === "admin" ? "active" : ""} onClick={() => setView("admin")}>
            Dead-letter admin
          </button>
        </nav>
      </header>

      {view === "dashboard" ? (
        <main>
          <UploadForm onJobCreated={handleJobCreated} />
          <div className="lanes">
            <section className="lane">
              <h3>High-priority lane</h3>
              {highLane.length === 0 && <p className="empty-state">No high-priority jobs yet.</p>}
              {highLane.map((job) => (
                <JobStatus key={job.id} job={job} onUpdate={handleJobUpdate} />
              ))}
            </section>
            <section className="lane">
              <h3>Low-priority lane</h3>
              {lowLane.length === 0 && <p className="empty-state">No low-priority jobs yet.</p>}
              {lowLane.map((job) => (
                <JobStatus key={job.id} job={job} onUpdate={handleJobUpdate} />
              ))}
            </section>
          </div>
        </main>
      ) : (
        <AdminDeadLetterView />
      )}
    </div>
  );
}