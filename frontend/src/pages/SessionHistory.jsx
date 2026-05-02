import React, { useState, useEffect } from "react";
import { FileText, Download, ShieldCheck } from "lucide-react";

export default function EvidencePage({ api }) {
  const [evidences, setEvidences] = useState([]);

  useEffect(() => {
    fetch(`${api}/api/v1/history/sessions?limit=50`)
      .then(res => res.json())
      .then(data => {
        // Map incidents to evidence format
        const mapped = (data.incidents || []).map(inc => ({
          id: inc.id,
          created_at: inc.timestamp,
          evidence_type: inc.incident_type,
          source: inc.zone_id || "DIGITAL",
          verdict: inc.risk_tier,
          sha256_hash: inc.evidence_hash || "hash_" + inc.id.substring(0, 16)
        }));
        setEvidences(mapped);
      })
      .catch(console.error);
  }, [api]);

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2>Evidence Center</h2>
        <p className="muted">Blockchain-hashed evidence logs for legal compliance</p>
      </div>

      <div className="panel">
        <h3>Evidence Records</h3>
        {evidences.length === 0 ? (
          <div className="empty-state">No evidence records found.</div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Created At</th>
                  <th>ID</th>
                  <th>Type / Source</th>
                  <th>Verdict</th>
                  <th>SHA-256 Hash</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {evidences.map(ev => (
                  <tr key={ev.id}>
                    <td>{new Date(ev.created_at).toLocaleString()}</td>
                    <td style={{ fontFamily: "monospace", fontSize: "12px", color: "var(--primary)" }}>{ev.id}</td>
                    <td>
                      <div>{ev.evidence_type}</div>
                      <div className="muted" style={{ fontSize: "12px" }}>{ev.source}</div>
                    </td>
                    <td>
                      <span className={`badge ${ev.verdict === 'SCAM' ? 'scam' : ev.verdict === 'SUSPICIOUS' ? 'suspicious' : 'safe'}`}>
                        {ev.verdict}
                      </span>
                    </td>
                    <td style={{ fontFamily: "monospace", fontSize: "11px", color: "var(--text-muted)", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis" }} title={ev.sha256_hash}>
                      <ShieldCheck size={12} color="var(--accent)" style={{ verticalAlign: "middle", marginRight: "4px" }}/>
                      {ev.sha256_hash.substring(0, 24)}...
                    </td>
                    <td>
                      <a href={`${api}/api/v1/evidence/${ev.id}/pdf`} target="_blank" rel="noopener noreferrer">
                        <button className="btn-primary" style={{ padding: "6px 12px", fontSize: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
                          <Download size={14} /> PDF
                        </button>
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
