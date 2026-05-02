import React, { useState, useEffect } from "react";
import { Users, Trash2, Plus } from "lucide-react";

export default function SettingsPage({ api }) {
  const [contacts, setContacts] = useState([]);
  const [formData, setFormData] = useState({ name: "", phone: "", upi_id: "" });

  useEffect(() => {
    fetchContacts();
  }, [api]);

  const fetchContacts = () => {
    fetch(`${api}/api/v1/contacts`)
      .then(res => res.json())
      .then(data => setContacts(data))
      .catch(console.error);
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!formData.name) return;
    try {
      await fetch(`${api}/api/v1/contacts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      setFormData({ name: "", phone: "", upi_id: "" });
      fetchContacts();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Remove this trusted contact?")) return;
    try {
      await fetch(`${api}/api/v1/contacts/${id}`, { method: "DELETE" });
      fetchContacts();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h2>Trusted Contacts</h2>
        <p className="muted">Manage contacts that bypass the ShieldGuard risk engine</p>
      </div>

      <div className="grid-2">
        <div className="panel">
          <h3>Add New Contact</h3>
          <form onSubmit={handleAdd} style={{ marginTop: "16px" }}>
            <div className="form-group">
              <label>Name</label>
              <input type="text" className="form-control" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} required />
            </div>
            <div className="form-group">
              <label>Phone Number</label>
              <input type="text" className="form-control" value={formData.phone} onChange={e => setFormData({...formData, phone: e.target.value})} />
            </div>
            <div className="form-group">
              <label>UPI ID (Optional)</label>
              <input type="text" className="form-control" value={formData.upi_id} onChange={e => setFormData({...formData, upi_id: e.target.value})} />
            </div>
            <button type="submit" className="btn-primary" style={{ width: "100%", marginTop: "8px" }}>
              <Plus size={16} style={{ verticalAlign: "middle", marginRight: "6px" }} /> Add Trusted Contact
            </button>
          </form>
        </div>

        <div className="panel">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h3>Current Directory</h3>
            <span className="badge monitor"><Users size={12} style={{ marginRight: "4px" }}/> {contacts.length}</span>
          </div>
          
          {contacts.length === 0 ? (
            <div className="empty-state">No trusted contacts added.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {contacts.map(c => (
                <div key={c.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px", background: "var(--bg)", borderRadius: "8px", border: "1px solid var(--border)" }}>
                  <div>
                    <div style={{ fontWeight: "600" }}>{c.name}</div>
                    <div className="muted" style={{ fontSize: "12px", marginTop: "4px" }}>
                      {c.phone && <span>📞 {c.phone}</span>}
                      {c.phone && c.upi_id && <span style={{ margin: "0 8px" }}>•</span>}
                      {c.upi_id && <span>💳 {c.upi_id}</span>}
                    </div>
                  </div>
                  <button onClick={() => handleDelete(c.id)} style={{ background: "transparent", border: "none", color: "var(--critical)", cursor: "pointer", padding: "8px" }}>
                    <Trash2 size={18} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
