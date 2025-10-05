import ValidationIcon from './ValidationIcon';

export interface PreviewRow {
  columns: string[];
  validations: { field: string; status: string; message?: string | null }[];
}

interface PreviewTableProps {
  headers: string[];
  rows: PreviewRow[];
}

const PreviewTable = ({ headers, rows }: PreviewTableProps) => {
  return (
    <div className="card">
      <table className="table">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header}>{header}</th>
            ))}
            <th>Validações</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              {row.columns.map((value, columnIndex) => (
                <td key={`${index}-${columnIndex}`}>{value}</td>
              ))}
              <td>
                {row.validations.map((validation) => (
                  <ValidationIcon
                    key={validation.field}
                    status={validation.status}
                    message={validation.message}
                  />
                ))}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PreviewTable;
