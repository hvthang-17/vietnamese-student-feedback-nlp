import { useEffect, useRef, useState } from 'react';
import { API, vi, labels, topics } from '../config';
import Badge from '../components/Badge';
import PieChart from '../components/PieChart';

export default function Dashboard() {
  const [filters, setFilters] = useState({ sentiment: '', topic: '', predicted_from: '', predicted_to: '' });
  const [page, setPage] = useState(1);
  const recordsScroll = useRef(null);
  const [pageSize, setPageSize] = useState(20);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => value).map(([key, value]) => [key, key.startsWith('predicted_') ? new Date(value).toISOString() : value])).toString();
  const invalid = filters.predicted_from && filters.predicted_to && filters.predicted_from >= filters.predicted_to;
  useEffect(() => {
    const controller = new AbortController();
    setData(previous => previous?.query === query ? previous : null);
    setError('');
    if (invalid) { setLoading(false); setError('Thời điểm kết thúc phải sau thời điểm bắt đầu.'); return; }
    setLoading(true);
    async function load() {
      try {
        const responses = await Promise.all([
          fetch(`${API}/api/v1/dashboard/summary?${query}`, { signal: controller.signal }),
          fetch(`${API}/api/v1/feedback?${query}&page=${page}&page_size=${pageSize}`, { signal: controller.signal })
        ]);
        if (responses.some(response => !response.ok)) throw new Error('Không thể tải dashboard. Kiểm tra kết nối và cấu hình API.');
        const [summary, records] = await Promise.all(responses.map(response => response.json()));
        if (!controller.signal.aborted) {
          setData({ summary, records, query });
          if (recordsScroll.current) recordsScroll.current.scrollTop = 0;
        }
      } catch (error) {
        if (!controller.signal.aborted) setError(error.message);
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }
    load();
    return () => controller.abort();
  }, [query, page, pageSize, retry, invalid]);
  function update(key, value) { setPage(1); setFilters(previous => ({ ...previous, [key]: value })); }
  async function exportFile(format) {
    setError('');
    try {
      const response = await fetch(`${API}/api/v1/exports/${format}?${query}`);
      if (!response.ok) { const body = await response.json(); throw new Error(typeof body.detail === 'string' ? body.detail : 'Không thể xuất báo cáo.'); }
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = `phan-hoi.${format}`;
      anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) { setError(error.message); }
  }
  return <main className="dashboard">
    <div className="page-title"><div><h1>Tổng quan phản hồi</h1></div>
      <p className="dashboard-subtitle">Tra cứu phản hồi hoặc xem tổng hợp theo cùng bộ lọc.</p></div>
    <div className="dashboard-toolbar"><div className="filter-heading"><button aria-expanded={filtersOpen} aria-controls="dashboard-filters" onClick={() => setFiltersOpen(value => !value)}>{filtersOpen ? 'Ẩn bộ lọc' : 'Mở bộ lọc'}</button><span>{Object.values(filters).filter(Boolean).length ? `${Object.values(filters).filter(Boolean).length} điều kiện đang áp dụng` : 'Đang xem tất cả phản hồi'}</span></div><div className="dashboard-exports"><span>Toàn bộ kết quả đã lọc</span><div className="actions">{['csv', 'pdf'].map(format => <button key={format} title="Xuất toàn bộ phản hồi khớp bộ lọc, không chỉ trang đang xem" disabled={!data || data.query !== query || loading || !!invalid} onClick={() => exportFile(format)}>Xuất {format.toUpperCase()}</button>)}</div></div></div>
    <section id="dashboard-filters" hidden={!filtersOpen} className="filters panel" aria-label="Bộ lọc phản hồi">
      {[['sentiment', 'Cảm xúc', labels], ['topic', 'Chủ đề', topics]].map(([key, title, values]) => <label key={key}>{title}<select value={filters[key]} onChange={event => update(key, event.target.value)}><option value="">Tất cả</option>{values.map(value => <option key={value} value={value}>{vi[value]}</option>)}</select></label>)}
      <label>Dự đoán từ (giờ máy bạn)<input type="datetime-local" value={filters.predicted_from} onChange={event => update('predicted_from', event.target.value)}/></label>
      <label>Đến trước (không bao gồm)<input type="datetime-local" value={filters.predicted_to} onChange={event => update('predicted_to', event.target.value)}/></label>
      <button onClick={() => { setPage(1); setFilters({ sentiment: '', topic: '', predicted_from: '', predicted_to: '' }); }}>Xóa bộ lọc</button>
    </section>
    {error && <div role="alert" className="error">{error} <button onClick={() => setRetry(value => value + 1)}>Thử lại</button></div>}
    {loading && !data && <p role="status">Đang tải dashboard…</p>}
    {data && <>
      <section className="kpis"><div className="kpi"><span>Tổng phản hồi theo bộ lọc</span><strong>{data.summary.total}</strong></div>{labels.map(label => <div className="kpi" key={label}><span>{vi[label]}</span><strong>{data.summary.sentiment[label]}</strong></div>)}</section>
      <div className="charts"><PieChart title="Phân bố cảm xúc" values={data.summary.sentiment}/><PieChart title="Phân bố chủ đề" values={data.summary.topic}/></div>
      <section className="panel table-panel"><h2>Chủ đề × cảm xúc</h2><div className="table-wrap"><table><caption>Số phản hồi trên toàn bộ dữ liệu khớp bộ lọc</caption><thead><tr><th scope="col">Chủ đề</th>{labels.map(label => <th scope="col" key={label}>{vi[label]}</th>)}</tr></thead><tbody>{topics.map(topic => <tr key={topic}><th scope="row">{vi[topic]}</th>{labels.map(label => <td key={label}>{data.summary.matrix[topic]?.[label] ?? 0}</td>)}</tr>)}</tbody></table></div></section>
      <section className="panel table-panel records-panel" aria-busy={loading}><div className="records-heading"><div><h2>Phản hồi đã phân tích</h2><p aria-live="polite">{loading ? 'Đang cập nhật phản hồi…' : data.records.total ? `${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, data.records.total)} trong ${data.records.total} phản hồi` : '0 phản hồi'}</p></div><nav className="record-pagination" aria-label="Phân trang"><label>Số dòng<select value={pageSize} disabled={loading} onChange={event => { setPage(1); setPageSize(Number(event.target.value)); }}>{[10, 20, 50, 100].map(size => <option key={size} value={size}>{size}</option>)}</select></label><button disabled={loading || page <= 1} onClick={() => setPage(value => value - 1)}>Trang trước</button><span aria-live="polite">Trang {page} / {Math.max(1, Math.ceil(data.records.total / pageSize))}</span><button disabled={loading || page * pageSize >= data.records.total} onClick={() => setPage(value => value + 1)}>Trang sau</button></nav></div>{data.records.items.length ? <div ref={recordsScroll} className="table-wrap records-scroll" tabIndex={0} role="region" aria-label="Danh sách phản hồi, cuộn để xem thêm"><table><thead><tr><th>Nội dung gốc</th><th>Cảm xúc</th><th>Chủ đề</th><th>Thời điểm dự đoán</th></tr></thead><tbody>{data.records.items.map(row => <tr key={row.id}><td className="raw-feedback">{row.raw_text ?? row.text}</td><td><Badge value={row.sentiment_label}/></td><td><Badge value={row.topic_label}/></td><td>{new Date(row.predicted_at).toLocaleString('vi-VN')}</td></tr>)}</tbody></table></div> : <p className="empty">Chưa có phản hồi phù hợp.</p>}
      </section>
    </>}
  </main>;
}
