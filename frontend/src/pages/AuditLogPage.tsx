import React, { useEffect, useState } from "react";
import { listAuditLog } from "../api/client";
import type { AuditLogEntry, AuditLogPage as AuditLogPageData } from "../api/types";

function fmtDate(iso: string) {
  return new Date(iso).toLocaleString("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function AuditLogPage() {
  const [data, setData] = useState<AuditLogPageData | null>(null);
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = (p = page) => {
    listAuditLog({ page: p, page_size: 50, action: actionFilter || undefined })
      .then(setData)
      .catch((err) => setError(String(err)));
  };

  useEffect(() => {
    load(page);
  }, [page]);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    load(1);
  }

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1 className="page-title">Audit Log</h1>
        {data && (
          <span className="text-gray-400 text-sm">{data.total} events</span>
        )}
      </div>

      {error && <div className="alert-error mb-4">{error}</div>}

      <form onSubmit={handleSearch} className="flex gap-2 mb-4">
        <input
          className="field-input max-w-xs"
          placeholder="Filter by action…"
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
        />
        <button type="submit" className="btn btn-ghost btn-sm">Filter</button>
      </form>

      {!data ? (
        <div className="empty-state">Loading…</div>
      ) : data.items.length === 0 ? (
        <div className="empty-state">No audit log entries.</div>
      ) : (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Target</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((entry: AuditLogEntry) => (
                <>
                  <tr
                    key={entry.id}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}
                  >
                    <td className="text-gray-500 whitespace-nowrap text-xs">
                      {fmtDate(entry.created_at)}
                    </td>
                    <td className="text-gray-700">{entry.actor_email || entry.actor_subject.slice(0, 8)}</td>
                    <td>
                      <span className="badge badge-purple">{entry.action}</span>
                    </td>
                    <td className="text-gray-500">
                      {entry.target_user_email || entry.target_user_id?.slice(0, 8) || "—"}
                    </td>
                    <td className="text-right text-gray-400 text-xs">
                      {expanded === entry.id ? "▲" : "▼"}
                    </td>
                  </tr>
                  {expanded === entry.id && (
                    <tr key={`${entry.id}-details`}>
                      <td colSpan={5} className="bg-gray-50 px-4 py-2">
                        <pre className="text-xs text-gray-600 whitespace-pre-wrap">
                          {JSON.stringify(entry.details ?? {}, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex gap-2 mt-4 justify-center items-center text-sm">
          <button
            className="btn btn-ghost btn-sm"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            ← Prev
          </button>
          <span className="text-gray-500">
            Page {page} of {totalPages}
          </span>
          <button
            className="btn btn-ghost btn-sm"
            disabled={page === totalPages}
            onClick={() => setPage(page + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
