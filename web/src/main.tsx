import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import App from './App';
import UploadPage from './pages/UploadPage';
import ResultPage from './pages/ResultPage';
import HistoryPage from './pages/HistoryPage';

import './styles.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<UploadPage />} />
          <Route path="jobs/:jobId" element={<ResultPage />} />
          <Route path="history" element={<HistoryPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
