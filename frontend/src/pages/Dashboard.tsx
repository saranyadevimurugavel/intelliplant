import { useQuery } from '@tanstack/react-query'
import { getHealth, getComplianceHealth, getRecommendations, getWarnings } from '../api/client'
import { AlertTriangle, Activity, FileText, ShieldCheck, Wrench, TrendingUp } from 'lucide-react'
import Badge from '../components/Badge'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const { data: health } = useQuery({ queryKey: ['health'], queryFn: () => getHealth().then(r => r.data) })
  const { data: compliance } = useQuery({ queryKey: ['compliance-health'], queryFn: () => getComplianceHealth().then(r => r.data) })
  const { data: recs } = useQuery({ queryKey: ['recommendations'], queryFn: () => getRecommendations().then(r => r.data) })
  const { data: warnings } = useQuery({ queryKey: ['warnings'], queryFn: () => getWarnings().then(r => r.data) })

  const criticalRecs = (recs ?? []).filter((r: any) => r.priority === 'critical')
  const highRecs = (recs ?? []).filter((r: any) => r.priority === 'high')

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Operations Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">Unified view of plant intelligence, maintenance status, and compliance health</p>
      </div>

      {/* Proactive Warnings Banner */}
      {warnings && warnings.length > 0 && (
        <div className="space-y-2">
          {warnings.map((w: any) => (
            <div key={w.id} className="flex gap-3 bg-red-950 border border-red-700 rounded-lg p-4">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-red-300 font-semibold text-sm">{w.warning_title}</p>
                <p className="text-red-400 text-xs mt-1">{w.warning_detail}</p>
                <p className="text-red-300 text-xs mt-2 font-medium">→ {w.recommended_action}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiCard
          title="Knowledge Graph"
          value={health?.knowledge_graph?.total_nodes ?? '—'}
          sub={`${health?.knowledge_graph?.total_edges ?? 0} edges`}
          icon={<Activity className="w-5 h-5 text-blue-400" />}
          color="blue"
        />
        <KpiCard
          title="Documents"
          value={health?.vector_store?.total_chunks ?? '—'}
          sub="indexed chunks"
          icon={<FileText className="w-5 h-5 text-purple-400" />}
          color="purple"
        />
        <KpiCard
          title="Compliance Score"
          value={compliance ? `${compliance.overall_score}%` : '—'}
          sub={`${compliance?.summary?.total_open_gaps ?? 0} open gaps`}
          icon={<ShieldCheck className="w-5 h-5 text-green-400" />}
          color={compliance?.summary?.critical > 0 ? 'red' : 'green'}
        />
        <KpiCard
          title="Maintenance Alerts"
          value={(criticalRecs.length + highRecs.length) || '—'}
          sub={`${criticalRecs.length} critical`}
          icon={<Wrench className="w-5 h-5 text-orange-400" />}
          color={criticalRecs.length > 0 ? 'red' : 'orange'}
        />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Maintenance Recommendations */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white flex items-center gap-2">
              <Wrench className="w-4 h-4 text-orange-400" /> Maintenance Recommendations
            </h2>
            <Link to="/maintenance" className="text-xs text-blue-400 hover:underline">View all →</Link>
          </div>
          <div className="space-y-3">
            {(recs ?? []).map((r: any) => (
              <div key={r.id} className="flex gap-3 bg-gray-800 rounded-lg p-3">
                <Badge label={r.priority} variant={r.priority as any} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200 font-medium truncate">{r.asset_tag} — {r.asset_name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{r.recommendation}</p>
                  <p className="text-xs text-gray-500 mt-1">Due: {r.predicted_failure_date}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Compliance Health */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-green-400" /> Compliance Health
            </h2>
            <Link to="/compliance" className="text-xs text-blue-400 hover:underline">View all →</Link>
          </div>
          {compliance && (
            <div className="space-y-3">
              {Object.entries(compliance.by_regulation ?? {}).map(([reg, data]: [string, any]) => (
                <div key={reg} className="flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-300 truncate">{reg}</span>
                      <span className="text-xs font-bold text-white ml-2">{data.score}%</span>
                    </div>
                    <div className="h-1.5 bg-gray-700 rounded-full">
                      <div
                        className={`h-1.5 rounded-full ${data.score >= 80 ? 'bg-green-500' : data.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${data.score}%` }}
                      />
                    </div>
                  </div>
                  {data.critical > 0 && <Badge label={`${data.critical} critical`} variant="critical" />}
                </div>
              ))}
              <div className="mt-4 flex gap-4 text-xs pt-3 border-t border-gray-700">
                <span className="text-red-400 font-semibold">{compliance.summary?.critical ?? 0} Critical</span>
                <span className="text-orange-400 font-semibold">{compliance.summary?.major ?? 0} Major</span>
                <span className="text-blue-400 font-semibold">{compliance.summary?.minor ?? 0} Minor</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
        <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-blue-400" /> Quick Actions
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { to: '/copilot', label: 'Ask the Copilot', desc: 'Query your documents', color: 'blue' },
            { to: '/documents', label: 'Upload Documents', desc: 'Ingest new files', color: 'purple' },
            { to: '/maintenance', label: 'Run RCA', desc: 'Analyse a failure', color: 'orange' },
            { to: '/compliance', label: 'Audit Package', desc: 'Generate evidence', color: 'green' },
          ].map(a => (
            <Link key={a.to} to={a.to} className="bg-gray-800 hover:bg-gray-700 rounded-lg p-3 transition-colors">
              <p className={`text-sm font-semibold text-${a.color}-400`}>{a.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{a.desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

function KpiCard({ title, value, sub, icon, color }: any) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-950 border-blue-800',
    purple: 'bg-purple-950 border-purple-800',
    green: 'bg-green-950 border-green-800',
    orange: 'bg-orange-950 border-orange-800',
    red: 'bg-red-950 border-red-800',
  }
  return (
    <div className={`rounded-xl border p-4 ${colorMap[color] ?? colorMap.blue}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
        </div>
        {icon}
      </div>
    </div>
  )
}
