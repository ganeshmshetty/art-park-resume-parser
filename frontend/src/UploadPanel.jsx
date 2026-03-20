import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

const DOMAINS = ["Technology", "Operations", "Sales", "Healthcare"];

function FileDropZone({ label, icon, file, onDrop, accept }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: useCallback((accepted) => { if (accepted[0]) onDrop(accepted[0]); }, [onDrop]),
    accept,
    multiple: false,
  });

  return (
    <div
      {...getRootProps()}
      className={`drop-zone${isDragActive ? " drag-over" : ""}${file ? " has-file" : ""}`}
    >
      <input {...getInputProps()} />
      <span className="drop-icon">{file ? "✅" : icon}</span>
      <div className="drop-label">{label}</div>
      <div className="drop-hint">
        {file ? "Click or drag to replace" : "Drag & drop or click to browse"}
      </div>
      <div className="drop-hint" style={{ marginTop: 4 }}>
        PDF, DOCX, or TXT
      </div>
      {file && (
        <div className="drop-filename" title={file.name}>
          📎 {file.name}
        </div>
      )}
    </div>
  );
}

export default function UploadPanel({ onSubmit, error }) {
  const [resume, setResume] = window.React.useState(null);
  const [jd, setJd] = window.React.useState(null);
  const [domain, setDomain] = window.React.useState("Technology");

  const ACCEPT = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    "text/plain": [".txt"],
  };

  function handleSubmit(e) {
    e.preventDefault();
    if (resume && jd) onSubmit({ resume, jd, domain });
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1 className="section-title">Analyze Your Profile</h1>
      <p className="section-subtitle">
        Upload your resume and a job description. Our AI computes your skill gap,
        builds a prerequisite-ordered learning pathway, and explains each recommendation
        with a grounded chain-of-thought trace.
      </p>

      <div className="upload-grid">
        <FileDropZone
          label="Resume"
          icon="📄"
          file={resume}
          onDrop={setResume}
          accept={ACCEPT}
        />
        <FileDropZone
          label="Job Description"
          icon="📋"
          file={jd}
          onDrop={setJd}
          accept={ACCEPT}
        />
      </div>

      <div className="domain-row">
        <span className="domain-label">Target Domain</span>
        <select
          id="domain-select"
          className="domain-select"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
        >
          {DOMAINS.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      {error && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      <button
        id="analyze-btn"
        type="submit"
        className="btn-analyze"
        disabled={!resume || !jd}
      >
        {resume && jd ? `🚀 Analyze — ${domain}` : "Select both files to continue"}
      </button>
    </form>
  );
}
