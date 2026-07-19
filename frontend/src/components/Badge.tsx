interface BadgeProps {
  label: string
  variant?: 'default' | 'critical' | 'major' | 'minor' | 'high' | 'medium' | 'low' | 'success' | 'warning' | 'info'
  className?: string
}

const styles: Record<string, string> = {
  default: 'bg-gray-700 text-gray-300',
  critical: 'bg-red-900 text-red-300 border border-red-700',
  high: 'bg-red-900 text-red-300 border border-red-700',
  major: 'bg-orange-900 text-orange-300 border border-orange-700',
  warning: 'bg-orange-900 text-orange-300 border border-orange-700',
  medium: 'bg-yellow-900 text-yellow-300 border border-yellow-700',
  minor: 'bg-blue-900 text-blue-300 border border-blue-700',
  info: 'bg-blue-900 text-blue-300 border border-blue-700',
  low: 'bg-gray-700 text-gray-300',
  success: 'bg-green-900 text-green-300 border border-green-700',
}

export default function Badge({ label, variant = 'default', className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${styles[variant] ?? styles.default} ${className}`}
    >
      {label}
    </span>
  )
}
