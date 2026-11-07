import { useEffect, useState } from 'react';
import Header from './components/Header';
import Analyze from './pages/Analyze';
import Dashboard from './pages/Dashboard';
import Import from './pages/Import';

export default function App() {
  const [page, setPage] = useState('analyze');
  const [collapsed, setCollapsed] = useState(() => window.matchMedia('(max-width: 760px)').matches);
  useEffect(() => {
    const mobile = window.matchMedia('(max-width: 760px)');
    const resize = event => setCollapsed(event.matches);
    mobile.addEventListener('change', resize);
    return () => mobile.removeEventListener('change', resize);
  }, []);
  function closeSidebar() {
    setCollapsed(true);
    document.querySelector('.sidebar-toggle')?.focus();
  }
  useEffect(() => {
    function escape(event) {
      if (event.key === 'Escape' && window.matchMedia('(max-width: 760px)').matches) closeSidebar();
    }
    document.addEventListener('keydown', escape);
    return () => document.removeEventListener('keydown', escape);
  }, []);
  function navigate(next) {
    setPage(next);
    if (window.matchMedia('(max-width: 760px)').matches) setCollapsed(true);
    window.scrollTo({ top: 0 });
  }
  return <div className={`app-shell${collapsed ? ' sidebar-collapsed' : ' sidebar-expanded'}`}>
    <Header page={page} setPage={navigate} collapsed={collapsed} onClose={closeSidebar}/>
    {!collapsed && <button className="sidebar-backdrop" aria-label="Đóng menu điều hướng" onClick={closeSidebar}/>}
    <div className={`workspace${page === 'dashboard' ? ' dashboard-workspace' : ''}`} id="workspace" tabIndex={-1}>
      <div className="workspace-bar"><div className="topbar-start"><button className="sidebar-toggle" aria-label={collapsed ? 'Mở rộng điều hướng' : 'Thu gọn điều hướng'} aria-expanded={!collapsed} aria-controls="main-navigation" onClick={() => setCollapsed(value => !value)}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg></button><span>Phản hồi sinh viên <span aria-hidden="true">/</span> {{ analyze: 'Phân tích', dashboard: 'Tổng quan', import: 'Nhập dữ liệu' }[page]}</span></div><span className="workspace-label">Cảm xúc & chủ đề</span></div>
      {page === 'analyze' ? <Analyze/> : page === 'dashboard' ? <Dashboard/> : <Import/>}
      <footer className="workspace-footer"><span>Góc lắng nghe</span><span>Hiểu phản hồi. Cải thiện trải nghiệm học tập.</span></footer>
    </div>
  </div>;
}
