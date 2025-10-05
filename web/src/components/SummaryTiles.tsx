interface SummaryTilesProps {
  items: { label: string; value: string | number }[];
}

const SummaryTiles = ({ items }: SummaryTilesProps) => (
  <div className="summary-grid">
    {items.map((item) => (
      <div key={item.label} className="summary-tile">
        <h3>{item.label}</h3>
        <p>{item.value}</p>
      </div>
    ))}
  </div>
);

export default SummaryTiles;
