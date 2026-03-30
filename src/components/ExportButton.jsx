export function ExportButton({ isExporting, progress, onExport, onCancel }) {
  if (isExporting) {
    const pct = Math.round(progress * 100);
    return (
      <div className="export-btn-wrap">
        <button className="btn-export recording" onClick={onCancel}>
          <span className="export-rec-dot">●</span>
          <span>RECORDING… {pct}%</span>
        </button>
        <div className="export-progress-bar">
          <div className="export-progress-fill" style={{ width: `${pct}%` }} />
        </div>
      </div>
    );
  }

  return (
    <button className="btn-export" onClick={onExport}>
      <span className="export-icon">⬇</span>
      EXPORT .WEBM
    </button>
  );
}
