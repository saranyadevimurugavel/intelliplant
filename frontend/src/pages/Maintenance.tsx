import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getRecommendations, getMaintenanceHistory, runRCA, getSchedule } from '../api/client'
import { Wrench, AlertTriangle, Calendar, ClipboardList, Loader2 } from 'lucide-react'
import Badge from '../components/Badge'

export default function Maintenance() {
  const [tab, setTab] = useState<'recs' | 'history' | 'rca' | 'schedule'>('recs')
  const [assetFilter, setAssetFilter] = useState('')
  const [rcaAsset, setRcaAsset] = useState('PUMP-P101')
  const [rcaDesc, setRcaDesc] = useState('')
  const [rcaResult, setRcaResult] = useState<any>(null)

  const { data: recs = [] } = useQuery({ queryKey: ['recommendations'], queryFn: () => getRecommendations().then(r => r.data) })
  const { data: history = [] } = useQuery({ queryKey: ['maintenance-history'], queryFn: () => getMaintenanceHistory().then(r => r.data) })
  const { data: schedule = [] } = useQuery({ queryKey: ['schedule'], queryFn: () => getSchedule().then(r => r.data) })

  const rcaMutation = useMutation({
    mutationFn: () => runRCA(rcaAsset, rcaDesc).then(r => r.data),
    onSuccess: setRcaResult,
  })

  const tabs = [
    { id: 'recs', label: 'Recommendations', icon: AlertTriangle },
    { id: 'history', label: 'Work History', icon: ClipboardList },
    { id: 'rca', label: 'RCA Agent', icon: Wrench },
    { id: 'schedule', label: 'Schedule', icon: Calendar },
  ] as const

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Maintenance Intelligence</h1>
        <p className="text-gray-400 text-sm mt-1">Predictive recommendations, work history, and AI-powered root cause analysis</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium flex-1 justify-center transition-colors ${
              tab === id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            <Icon className="w-4 h-4" />
            <span className="hidden sm:inline">{label}</span>
          </button>
        ))}
      </div>

      {/* Recommendations */}
      {tab === 'recs' && (
        <div className="space-y-4">
          {(recs as any[]).map(r => (
            <div key={r.id} className={`bg-gray-900 border rounded-xl p-5 ${r.priority === 'critical' ? 'border-red-700' : r.priority === 'high' ? 'border-orange-700' : 'border-gray-800'}`}>
              <div className="flex items-start gap-3">
                <Badge label={r.priority} variant={r.priority as any} />
                <Badge label={r.type} variant="info" />
                <div className="flex-1">
                  <p className="text-white font-semibold">{r.asset_tag} — {r.asset_name}</p>
                  <p className="text-gray-300 text-sm mt-1">{r.recommendation}</p>
                  <p className="text-gray-400 text-xs mt-2">{r.basis}</p>
                  <div className="flex flex-wrap gap-4 mt-3 text-xs text-gray-500">
                    <span>⏰ Action by: <span className="text-orange-400 font-medium">{r.predicted_failure_date}</span></span>
                    <span>⏱ Est. downtime: {r.estimated_downtime}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {r.relevant_documents?.map((d: string) => (
                      <span key={d} className="text-xs bg-gray-800 text-blue-300 px-2 py-0.5 rounded">{d}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Work History */}
      {tab === 'history' && (
        <div className="space-y-3">
          {(history as any[]).map((r, i) => (
            <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-blue-400 font-mono text-sm">{r.work_order_id}</span>
                    <Badge label={r.type} variant="info" />
                    <Badge label={r.asset_tag} />
                  </div>
                  <p className="text-white text-sm mt-1">{r.description}</p>
                  <p className="text-gray-400 text-xs mt-1">{r.findings}</p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    {r.completed_date && <span>Completed: {r.completed_date}</span>}
                    {r.technician && <span>Tech: {r.technician}</span>}
                    {r.downtime_hours && <span>Downtime: {r.downtime_hours}h</span>}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* RCA Agent */}
      {tab === 'rca' && (
        <div className="space-y-5">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
            <h3 className="text-white font-semibold">Root Cause Analysis Agent</h3>
            <p className="text-gray-400 text-sm">Describe a failure or abnormal event and the AI will analyse maintenance history and knowledge base to identify the root cause.</p>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Asset Tag</label>
                <input
                  value={rcaAsset}
                  onChange={e => setRcaAsset(e.target.value)}
                  placeholder="e.g. PUMP-P101"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Failure Description</label>
                <textarea
                  value={rcaDesc}
                  onChange={e => setRcaDesc(e.target.value)}
                  placeholder="Describe the failure, symptoms, and when it occurred..."
                  rows={4}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 outline-none focus:border-blue-500 resize-none"
                />
              </div>
              <button
                onClick={() => rcaMutation.mutate()}
                disabled={!rcaAsset || !rcaDesc || rcaMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {rcaMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wrench className="w-4 h-4" />}
                {rcaMutation.isPending ? 'Analysing...' : 'Run RCA Analysis'}
              </button>
            </div>
          </div>

          {rcaResult && (
            <div className="bg-gray-900 border border-blue-800 rounded-xl p-5">
              <h3 className="text-white font-semibold mb-3">RCA Results — {rcaResult.asset_tag}</h3>
              <pre className="whitespace-pre-wrap font-sans text-sm text-gray-300 leading-relaxed">{rcaResult.rca_analysis}</pre>
              <p className="text-xs text-gray-500 mt-4">Generated: {new Date(rcaResult.generated_at).toLocaleString()}</p>
            </div>
          )}
        </div>
      )}

      {/* Schedule */}
      {tab === 'schedule' && (
        <div className="space-y-3">
          {(schedule as any[]).map((s, i) => (
            <div key={i} className={`bg-gray-900 border rounded-xl p-4 ${s.priority === 'critical' ? 'border-red-700' : s.priority === 'high' ? 'border-orange-700' : 'border-gray-800'}`}>
              <div className="flex items-start gap-3">
                <Calendar className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-blue-400 font-mono text-sm">{s.work_order_id}</span>
                    <Badge label={s.priority} variant={s.priority as any} />
                    <Badge label={s.status} variant={s.status === 'in_progress' ? 'warning' : 'info'} />
                  </div>
                  <p className="text-white text-sm mt-1">{s.asset_tag} — {s.asset_name}</p>
                  <p className="text-gray-400 text-sm">{s.work_type}</p>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span>Start: {s.start_date}</span>
                    <span>Estimated end: {s.estimated_completion}</span>
                    {s.technician !== 'TBD' && <span>Assigned: {s.technician}</span>}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
