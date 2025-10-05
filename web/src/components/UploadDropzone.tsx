import { useCallback, useState } from 'react';

interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
  disabled?: boolean;
}

const UploadDropzone = ({ onUpload, disabled }: UploadDropzoneProps) => {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || !files[0]) return;
      setError(null);
      try {
        await onUpload(files[0]);
      } catch (err) {
        setError((err as Error).message);
      }
    },
    [onUpload],
  );

  return (
    <div
      className={`card upload-dropzone ${dragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        if (!disabled) {
          handleFiles(event.dataTransfer.files);
        }
      }}
    >
      <input
        id="upload-input"
        type="file"
        style={{ display: 'none' }}
        onChange={(event) => handleFiles(event.target.files)}
        disabled={disabled}
      />
      <label htmlFor="upload-input" className="upload-label">
        <strong>Arraste e solte</strong> ou clique para selecionar um arquivo
      </label>
      {error && <p className="error">{error}</p>}
    </div>
  );
};

export default UploadDropzone;
