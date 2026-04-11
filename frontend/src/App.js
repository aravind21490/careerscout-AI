import { useState, useEffect } from "react";
import "./App.css";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

function ScoreBadge({ score }) {
  const color =
    score >= 8 ? "#16a34a" : score >= 6 ? "#d97706" : "#dc2626";
  return (
    <span style={{
      background: color + "20",
      color,
      border: `1px solid ${color}40`,
      borderRadius: 6,
      padding: "2px 10px",
      fontWeight: 600,
      fontSize: 13,
    }}>
      {score}/10
    </span>
  );
}

function TypeBadge({ type }) {
  const map = {
    internship: { bg: "#dbeafe", color: "#1d4ed8", label: "Internship" },
    hackathon:  { bg: "#fce7f3", color: "#be185d", label: "Hackathon" },
    job:        { bg: "#dcfce7", color: "#15803d", label: "Job" },
  };
  const style = map[type] || { bg: "#f3f4f6", color: "#374151", label: type };
  return (
    <span style={{
      background: style.bg,
      color: style.color,
      borderRadius: 6,
      padding: "2px 10px",
      fontSize: 12,
      fontWeight: 500,
    }}>
      {style.label}
    </span>
  );
}

function JobCard({ job, index }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="job-card" style={{ animationDelay: `${index * 60}ms` }}>
      <div className="job-card-header">
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6, flexWrap: "wrap" }}>
            <TypeBadge type={job.type} />
            <span style={{ fontSize: 12, color: "#6b7280" }}>{job.source}</span>
          </div>
          <h3 className="job-title">{job.title}</h3>
          <div style={{ display: "flex", gap: 12, marginTop: 6, flexWrap: "wrap" }}>
            {job.domain && <span className="meta-tag">📡 {job.domain}</span>}
            {job.location && <span className="meta-tag">📍 {job.location}</span>}
            {job.stipend && <span className="meta-tag">💰 {job.stipend}</span>}
            {job.deadline && <span className="meta-tag">⏰ {job.deadline}</span>}
          </div>
        </div>
        <ScoreBadge score={job.score} />
      </div>

      {job.skills?.length > 0 && (
        <div className="skills-row">
          {job.skills.map((s, i) => (
            <span key={i} className="skill-chip">{s}</span>
          ))}
        </div>
      )}

      <div style={{ display: "flex", gap: 10, marginTop: 12, alignItems: "center" }}>
        <a href={job.link} target="_blank" rel="noreferrer" className="btn-apply">
          Apply →
        </a>
        <button className="btn-ghost" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Hide AI reasoning" : "Why matched?"}
        </button>
      </div>

      {expanded && job.reasoning && (
        <div className="reasoning-box">
          <span className="reasoning-label">AI reasoning</span>
          <p>{job.reasoning}</p>
        </div>
      )}
    </div>
  );
}

function ResumeAnalyzer() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch(`${API}/resume`, { method: "POST", body: form });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      setResult(data);
    } catch {
      setError("Could not analyze resume. Make sure the API is running.");
    } finally {
      setLoading(false);
    }
  }

  const scoreColor = result
    ? result.ats_score >= 70 ? "#16a34a"
    : result.ats_score >= 50 ? "#d97706"
    : "#dc2626"
    : "#6b7280";

  return (
    <div className="resume-section">
      <h2 className="section-title">ATS Resume Optimizer</h2>
      <p className="section-sub">Upload your PDF resume — get an instant ATS score + keyword suggestions powered by Groq LLaMA.</p>
      <label className="upload-area">
        <input type="file" accept=".pdf" onChange={handleUpload} style={{ display: "none" }} />
        <div className="upload-inner">
          <span style={{ fontSize: 32 }}>📄</span>
          <span>{loading ? "Analyzing..." : "Click to upload resume (PDF)"}</span>
          {loading && <div className="spinner" />}
        </div>
      </label>
      {error && <div className="error-box">{error}</div>}
      {result && (
        <div className="ats-result">
          <div className="ats-score-row">
            <div className="ats-score-circle" style={{ borderColor: scoreColor, color: scoreColor }}>
              <span className="ats-score-num">{result.ats_score}</span>
              <span className="ats-score-label">/100</span>
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 4 }}>
                {result.verdict === "strong" ? "✅ Strong resume"
                : result.verdict === "average" ? "⚠️ Needs some work"
                : "❌ Needs significant improvement"}
              </div>
              <p style={{ color: "#6b7280", fontSize: 14 }}>{result.summary}</p>
            </div>
          </div>
          <div className="ats-grid">
            <div className="ats-card green">
              <h4>Strong keywords</h4>
              <div className="chip-list">
                {result.strong_keywords?.map((k, i) => <span key={i} className="chip green">{k}</span>)}
              </div>
            </div>
            <div className="ats-card red">
              <h4>Missing keywords</h4>
              <div className="chip-list">
                {result.missing_keywords?.map((k, i) => <span key={i} className="chip red">{k}</span>)}
              </div>
            </div>
          </div>
          <div style={{ marginTop: 16 }}>
            <h4 style={{ marginBottom: 8 }}>Improvements</h4>
            {result.improvements?.map((tip, i) => (
              <div key={i} className={`tip-row ${tip.priority}`}>
                <span className="tip-badge">{tip.priority}</span>
                <span>{tip.tip}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [filter, setFilter] = useState("all");
  const [tab, setTab] = useState("jobs");
  const [runResult, setRunResult] = useState(null);
  const [stats, setStats] = useState({ total: 0, internships: 0, hackathons: 0 });

  async function fetchJobs(type) {
    setLoading(true);
    try {
      const url = type && type !== "all"
        ? `${API}/jobs?limit=50&type=${type}`
        : `${API}/jobs?limit=50`;
      const res = await fetch(url);
      const data = await res.json();
      setJobs(data.jobs || []);
      setStats({
        total: data.count,
        internships: data.jobs?.filter(j => j.type === "internship").length || 0,
        hackathons: data.jobs?.filter(j => j.type === "hackathon").length || 0,
      });
    } catch {
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }

  async function triggerRun() {
    setRunning(true);
    setRunResult(null);
    try {
      const res = await fetch(`${API}/run`, { method: "POST" });
      const data = await res.json();
      setRunResult(data);
      fetchJobs(filter === "all" ? null : filter);
    } catch {
      setRunResult({ status: "error" });
    } finally {
      setRunning(false);
    }
  }

  useEffect(() => { fetchJobs(); }, []);

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div>
            <div className="logo">🎯 CareerScout AI</div>
            <div className="tagline">AI-powered internship & hackathon finder</div>
          </div>
          <button className={`btn-run ${running ? "running" : ""}`} onClick={triggerRun} disabled={running}>
            {running ? "⟳ Running pipeline..." : "▶ Run Pipeline"}
          </button>
        </div>
        {runResult && (
          <div className={`run-result ${runResult.status}`}>
            {runResult.status === "success"
              ? `✅ Done — scraped ${runResult.scraped}, found ${runResult.recommended} new matches`
              : "❌ Pipeline error — check API logs"}
          </div>
        )}
        <div className="stats-bar">
          <div className="stat"><span className="stat-num">{stats.total}</span><span className="stat-label">total matches</span></div>
          <div className="stat-divider" />
          <div className="stat"><span className="stat-num">{stats.internships}</span><span className="stat-label">internships</span></div>
          <div className="stat-divider" />
          <div className="stat"><span className="stat-num">{stats.hackathons}</span><span className="stat-label">hackathons</span></div>
          <div className="stat-divider" />
          <div className="stat"><span className="stat-num">3</span><span className="stat-label">AI chain steps</span></div>
        </div>
      </header>

      <div className="tabs">
        <button className={`tab ${tab === "jobs" ? "active" : ""}`} onClick={() => setTab("jobs")}>Job Feed</button>
        <button className={`tab ${tab === "resume" ? "active" : ""}`} onClick={() => setTab("resume")}>Resume Optimizer</button>
      </div>

      <main className="main">
        {tab === "jobs" && (
          <>
            <div className="filter-bar">
              {["all", "internship", "hackathon", "job"].map(f => (
                <button
                  key={f}
                  className={`filter-btn ${filter === f ? "active" : ""}`}
                  onClick={() => { setFilter(f); fetchJobs(f === "all" ? null : f); }}
                >
                  {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
            {loading ? (
              <div className="loading-state">
                <div className="spinner large" />
                <p>Fetching AI-filtered listings...</p>
              </div>
            ) : jobs.length === 0 ? (
              <div className="empty-state">
                <p>No listings yet. Click <strong>Run Pipeline</strong> to scrape and filter jobs.</p>
              </div>
            ) : (
              <div className="job-list">
                {jobs.map((job, i) => <JobCard key={job.id} job={job} index={i} />)}
              </div>
            )}
          </>
        )}
        {tab === "resume" && <ResumeAnalyzer />}
      </main>
    </div>
  );
}