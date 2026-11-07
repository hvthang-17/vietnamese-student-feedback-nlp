import { useState } from 'react';
import { API } from '../config';

export default function Import() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  async function submit(event) {
    event.preventDefault(); setResult(null); setError('');
    if (!file) { setError('Chọn tệp CSV trước khi nhập.'); return; }
    setLoading(true);
    const form = new FormData(); form.append('file', file);
    try {
      const response = await fetch(`${API}/api/v1/imports/csv`, { method: 'POST', body: form });
      const json = await response.json();
      if (!response.ok) throw new Error(typeof json.detail === 'string' ? json.detail : 'Không thể nhập tệp. Kiểm tra cấu trúc CSV rồi thử lại.');
      setResult(json);
    } catch (error) { setError(error.message); } finally { setLoading(false); }
  }
  return <main className="import"><div className="page-title"><div><h1>Từ nhiều phản hồi,<br/>đến một cái nhìn chung.</h1><p>Nhập tệp CSV để phân tích và lưu nhiều phản hồi cùng lúc.</p></div></div><div className="import-layout"><section className="panel upload-panel"><form onSubmit={submit} aria-busy={loading}><label htmlFor="csv">Chọn tệp phản hồi</label><div className="file-picker"><span className="file-symbol" aria-hidden="true">CSV</span><p>{file ? file.name : 'Tệp CSV từ máy tính của bạn'}</p><input id="csv" type="file" accept=".csv,text/csv" disabled={loading} onChange={event => { setFile(event.target.files?.[0] || null); setResult(null); setError(''); }}/><small>UTF-8, tối đa 2 MB và 1.000 dòng theo cấu hình mặc định.</small></div><button className="primary" disabled={loading}>{loading ? 'Đang nhập và phân tích…' : 'Nhập và phân tích'}</button>{error && <p className="error" role="alert">{error}</p>}</form>{result && <div className="import-result" aria-live="polite"><strong>Đã nhập {result.imported} phản hồi</strong><p>Xem dữ liệu đã lưu tại Tổng quan dữ liệu.</p>{result.errors.length > 0 && <details><summary>{result.errors.length} dòng cần kiểm tra</summary><ul>{result.errors.map(item => <li key={item.row}>Dòng {item.row}: {item.message}</li>)}</ul></details>}</div>}</section><aside className="csv-guide"><h2>Chuẩn bị tệp của bạn</h2><p>Mỗi dòng là một phản hồi. Cột <code>text</code> là bắt buộc.</p><pre>text{'\n'}"Giảng viên rất nhiệt tình."{'\n'}"Phòng học cần thêm quạt."</pre><p>Có thể thêm cột <code>created_at</code> ở định dạng ISO 8601 có múi giờ.</p><p className="privacy-note">Bỏ thông tin nhận diện cá nhân trước khi nhập. Các dòng hợp lệ được lưu; dòng không hợp lệ được báo riêng.</p></aside></div></main>;
}
