import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import UploadDropzone from '../components/UploadDropzone';
import SummaryTiles from '../components/SummaryTiles';
import useJobs from '../hooks/useJobs';
import axios from '../api';

const UploadPage = () => {
  const navigate = useNavigate();
  const { jobs, refresh } = useJobs();
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const response = await axios.post('/jobs/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await refresh();
      navigate(`/jobs/${response.data.job_id}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-page">
      <UploadDropzone onUpload={handleUpload} disabled={uploading} />
      <SummaryTiles
        items={[
          { label: 'Total de Jobs', value: jobs.length },
          { label: 'Em processamento', value: jobs.filter((job) => job.status === 'processing').length },
          { label: 'Aprovados', value: jobs.filter((job) => job.status === 'approved').length },
        ]}
      />
    </div>
  );
};

export default UploadPage;
