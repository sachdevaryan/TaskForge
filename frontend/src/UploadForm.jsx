import { useState } from "react";
import { createJob } from "./api";

export default function UploadForm({ onJobCreated }) {
  const [file, setFile] = useState(null);
  const [priority, setPriority] = useState("low");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      setError("Choose a file first.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const job = await createJob(file, priority);
      onJobCreated(job);
      setFile(null);
      e.target.reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <h2>Submit a file</h2>
      <input
        type="file"
        accept="image/*"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <div className="priority-toggle">
        <label>
          <input
            type="radio"
            name="priority"
            value="low"
            checked={priority === "low"}
            onChange={() => setPriority("low")}
          />
          Low priority
        </label>
        <label>
          <input
            type="radio"
            name="priority"
            value="high"
            checked={priority === "high"}
            onChange={() => setPriority("high")}
          />
          High priority
        </label>
      </div>
      <button type="submit" disabled={submitting}>
        {submitting ? "Submitting…" : "Submit job"}
      </button>
      {error && <p className="error-text">{error}</p>}
    </form>
  );
}