import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import PreviewTable, { PreviewRow } from '../components/PreviewTable';
import axios from '../api';

interface PreviewResponse {
  job_id: string;
  headers: string[];
  rows: PreviewRow[];
  total_rows: number;
  metadata: Record<string, unknown>;
}

const ResultPage = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [status, setStatus] = useState<string>('');

  useEffect(() => {
    const load = async () => {
      if (!jobId) return;
      const [jobResponse, previewResponse] = await Promise.all([
        axios.get(`/jobs/${jobId}`),
        axios.get(`/preview/${jobId}`).catch(() => null),
      ]);
      setStatus(jobResponse.data.status);
      if (previewResponse) {
        setPreview(previewResponse.data);
      }
    };
    load();
  }, [jobId]);

  const handleDownload = () => {
    if (!jobId) return;
    window.location.href = `${axios.defaults.baseURL}/download/${jobId}`;
  };

  const handleApprove = async () => {
    if (!jobId) return;
    await axios.post(`/approval/${jobId}`, { approver: 'admin' });
    navigate('/history');
  };

  return (
    <div className="result-page">
      <div className="card">
        <h2>Job {jobId}</h2>
        <p>Status atual: {status}</p>
        <button onClick={handleDownload} disabled={!preview}>
          Baixar CSV
        </button>
        <button onClick={handleApprove} disabled={status !== 'completed'}>
          Aprovar
        </button>
        <Link to="/">Voltar</Link>
      </div>
      {preview && <PreviewTable headers={preview.headers} rows={preview.rows} />}
    </div>
  );
};

export default ResultPage;
