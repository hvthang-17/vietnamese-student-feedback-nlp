import { useId } from 'react';
import { vi } from '../config';

const percent = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 });
const count = new Intl.NumberFormat('vi-VN');

export default function PieChart({ title, values }) {
  const titleId = useId();
  const entries = Object.entries(values);
  const total = entries.reduce((sum, [, value]) => sum + value, 0);
  let offset = 0;
  return <section className="chart panel" aria-labelledby={titleId}>
    <h2 id={titleId}>{title}</h2>
    <p className="chart-note">Tỷ trọng phản hồi theo bộ lọc hiện tại</p>
    <div className="pie-layout">
      <div className="donut">
        <svg viewBox="0 0 180 180" aria-hidden="true">
          <circle className="donut-track" cx="90" cy="90" r="70" fill="none" strokeWidth="26"/>
          {total > 0 && entries.map(([key, value]) => {
            const share = value / total * 100;
            const start = offset;
            offset += share;
            return value > 0 && <circle key={key} className={`donut-slice chart-color-${key}`} cx="90" cy="90" r="70" fill="none" strokeWidth="26" pathLength="100" strokeDasharray={`${share} ${100 - share}`} strokeDashoffset={-start} transform="rotate(-90 90 90)"/>;
          })}
        </svg>
        <div className="donut-total"><strong>{count.format(total)}</strong><span>phản hồi</span></div>
      </div>
      <ul className="pie-legend">
        {entries.map(([key, value]) => <li key={key}>
          <span className={`legend-dot chart-color-${key}`} aria-hidden="true"/>
          <span className="legend-label">{vi[key] || key}</span>
          <span className="legend-value"><strong>{count.format(value)}</strong><span>{percent.format(total ? value / total * 100 : 0)}%</span></span>
        </li>)}
      </ul>
    </div>
    {total === 0 && <p className="chart-empty">Chưa có dữ liệu phù hợp với bộ lọc.</p>}
  </section>;
}
