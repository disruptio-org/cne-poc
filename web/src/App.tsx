import { Link, Outlet, useLocation } from 'react-router-dom';

function App() {
  const location = useLocation();
  return (
    <div className="app">
      <header className="app__header">
        <h1>CNE Processamento</h1>
        <nav>
          <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
            Upload
          </Link>
          <Link to="/history" className={location.pathname.includes('history') ? 'active' : ''}>
            Histórico
          </Link>
        </nav>
      </header>
      <main className="app__main">
        <Outlet />
      </main>
    </div>
  );
}

export default App;
