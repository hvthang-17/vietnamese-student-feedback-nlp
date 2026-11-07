import { useState } from 'react';
import { API } from '../config';
import Badge from '../components/Badge';
import ResultDetails from '../components/ResultDetails';

const examples = [
  ['Về giảng viên', 'Giảng viên rất nhiệt tình và bài giảng dễ hiểu.'],
  ['Về cơ sở vật chất', 'Phòng học nóng và wifi thường xuyên bị ngắt.'],
  ['Về chương trình học', 'Chương trình học cần thêm các buổi thực hành.'],
];

export default function Analyze() {
  const [text, setText] = useState('');
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  function edit(value) { setText(value); setData(null); setError(''); }
  async function submit(event) {
    event.preventDefault(); setError(''); setData(null);
    if (!text.trim()) { setError('Nhập nội dung phản hồi trước khi phân tích.'); return; }
    setLoading(true);
    try {
      const response = await fetch(`${API}/api/v1/predictions`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
      const json = await response.json();
      if (!response.ok) throw new Error(json.detail?.[0]?.msg || (typeof json.detail === 'string' && json.detail) || 'Chưa thể phân tích. Kiểm tra kết nối API rồi thử lại.');
      setData(json);
    } catch (error) { setError(error.message); } finally { setLoading(false); }
  }
  return <main className="analyze"><section className="hero"><h1>Lắng nghe từ<br/>những điều sinh viên chia sẻ.</h1><p>Đọc cảm xúc, nhận diện chủ đề. Bắt đầu từ một phản hồi bằng tiếng Việt.</p></section>
    <div className="analysis-layout"><div className="analysis-column"><section className="panel composer"><form onSubmit={submit} aria-busy={loading}><div className="section-heading"><label htmlFor="feedback">Bạn muốn phân tích phản hồi nào?</label><span className="field-hint">Tiếng Việt</span></div><textarea id="feedback" value={text} disabled={loading} onChange={event => edit(event.target.value)} maxLength={5000} aria-describedby="feedback-help" placeholder="Nhập lời chia sẻ của sinh viên tại đây…"/><div className="form-bottom"><span id="feedback-help">{text.length.toLocaleString('vi-VN')} / 5.000 ký tự</span><button className="primary" disabled={loading}>{loading ? 'Đang phân tích…' : 'Phân tích phản hồi'}</button></div>{error && <p className="error" role="alert">{error}</p>}</form></section>
      <div className="examples"><span>Thử một câu mẫu</span><div>{examples.map(([label, value]) => <button key={label} disabled={loading} onClick={() => edit(value)}>{label}</button>)}</div></div>
      <section className={data ? 'result' : 'result result-empty'} aria-live="polite" aria-busy={loading}>{data ? <><div className="section-heading"><h2>Kết quả phân tích</h2><span className="saved-state">Đã lưu phản hồi</span></div><blockquote>{data.raw_text ?? data.text}</blockquote><div className="result-grid">{[['sentiment', 'Cảm xúc'], ['topic', 'Chủ đề']].map(([key, name]) => <div key={key}><span>{name}</span><Badge value={data[`${key}_label`]}/><div className="confidence-track" aria-hidden="true"><i style={{ width: `${data[`${key}_confidence`] * 100}%` }}/></div><small>{Math.round(data[`${key}_confidence`] * 100)}% điểm tin cậy</small></div>)}</div><ResultDetails result={data}/></> : <><span className="empty-result-mark" aria-hidden="true">“ ”</span><h2>{loading ? 'Đang đọc phản hồi của bạn…' : 'Một phản hồi, hai góc nhìn'}</h2><p>{loading ? 'Kết quả cảm xúc và chủ đề sẽ xuất hiện tại đây.' : 'Nhập nội dung và chọn phân tích để xem cảm xúc, chủ đề và điểm tin cậy.'}</p></>}</section>
    </div><aside className="analysis-guide"><div className="guide-illustration" aria-hidden="true"><div className="quote-sheet"><span>“</span><div/><div/><div/></div><span className="illustration-tag">Lời chia sẻ</span></div><h2>Phản hồi đang nói điều gì?</h2><p>Hai mô hình đọc cùng một nội dung, mỗi mô hình trả lời một câu hỏi.</p><div className="guide-part"><span className="guide-dot sentiment-dot"/><div><h3>Cảm xúc như thế nào?</h3><p>Tiêu cực, trung tính hoặc tích cực.</p></div></div><div className="guide-part"><span className="guide-dot topic-dot"/><div><h3>Đang nói về điều gì?</h3><p>Giảng viên, chương trình đào tạo, cơ sở vật chất hoặc chủ đề khác.</p></div></div><div className="privacy-note">Trước khi nhập, hãy bỏ tên, mã sinh viên và thông tin nhận diện cá nhân.</div></aside></div>
  </main>;
}
