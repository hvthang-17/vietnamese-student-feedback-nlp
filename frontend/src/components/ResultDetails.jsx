const percentage = new Intl.NumberFormat('vi-VN', {
  style: 'percent', minimumFractionDigits: 2, maximumFractionDigits: 2,
});

export default function ResultDetails({ result }) {
  return <details className="model-details">
    <summary>Về kết quả này</summary>
    <div className="result-explanation">
      <p className="explanation-intro">Hai điểm tin cậy, hai tác vụ độc lập.</p>
      <dl className="confidence-facts">
        {[
          ['sentiment_confidence', 'Độ tin cậy cảm xúc'],
          ['topic_confidence', 'Độ tin cậy chủ đề'],
        ].map(([key, label]) => <div className="confidence-fact" key={key}>
          <dt>{label}</dt>
          <dd><strong>{percentage.format(result[key])}</strong><span className="original-confidence">Giá trị gốc <span>{result[key]}</span></span></dd>
        </div>)}
        <div className="model-fact"><dt>Mã mô hình</dt><dd><span className="model-identity">{result.model_version}</span><span className="model-hint">Dùng để xác định bộ mô hình đã tạo ra kết quả này.</span></dd></div>
      </dl>
      <p className="confidence-caveat"><span aria-hidden="true">i</span>Điểm tin cậy cho biết mức mô hình nghiêng về nhãn đã chọn, không phải tỷ lệ chắc chắn đúng. Kết quả hỗ trợ tổng hợp và cần được xem xét theo ngữ cảnh.</p>
    </div>
  </details>;
}
