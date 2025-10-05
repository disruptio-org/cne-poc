interface ValidationIconProps {
  status: string;
  message?: string | null;
}

const ValidationIcon = ({ status, message }: ValidationIconProps) => {
  const className = status === 'ok' ? 'badge ok' : 'badge warning';
  return <span className={className} title={message ?? undefined}>{status.toUpperCase()}</span>;
};

export default ValidationIcon;
