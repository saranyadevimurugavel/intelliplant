import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getComplianceGaps, getComplianceHealth, generateAuditPackage } from '../api/client'
import { ShieldCheck, AlertTriangle, FileDown, Loader2 } from 'lucide-react'
import Badge from '../components/Badge'

const REGULATIONS = ['OISD-STD-116', 'PESO', 'Factories Act 1948', 'CPCB']

export default function Compliance() {
  const [tab, setTab] = useState<'gaps' | 'health' | 'audit'>('gaps')
  const [auditReg, setAuditReg] = useState(REGULATIONS[0])
  const [auditResult, setAuditResult] = useState<any>(null)
  const [sevFilter, setSevFilter] = useState('')

  const { data: health } = useQuery({ queryKey: ['compliance-health'], queryFn: () => getComplianceHealth().then(r => r.data) })
  const { data: gaps = [] } = useQuery({ queryKey: ['compliance-gaps', sevFilter], queryFn: () => getComplianceGaps({ severity: sevFilter || undefined } as any).then(r => r.data) })

  const auditMutation = useMutation({
    mutationFn: () => generateAuditPackage(auditReg).then(r => r.data),
    onSuccess: setAuditResult,
  })

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Compliance Intelligence</h1>
        <p className="text-gray-400 text-sm mt-1">Regulatory gap detection, compliance health, and audit evidence generation</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1">
        {(['gaps', 'health', 'audit'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${tab === t ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-gray-200'}`}
          >
            {t === 'gaps' ? 'Compliance Gaps' : t === 'health' ? 'Health Dashboard' : 'Audit Package'}
          </button>
        ))}
      </div>

      {/* Gaps */}
      {tab === 'gaps' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            {['', 'critical', 'major', 'minor'].map(s => (
              <button
                key={s}
                onClick={() => setSevFilter(s)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${sevFilter === s ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-gray-200'}`}
              >
                {s || 'All'}
              </button>
            ))}
          </div>

          {(gaps as any[]).map(g => (
            <div key={g.id} className={`bg-gray-900 border rounded-xl p-5 ${g.severity === 'critical' ? 'border-red-700' : g.severity === 'major' ? 'border-orange-700' : 'border-gray-800'}`}>
              <div className="flex items-start gap-3">
                <AlertTriangle className={`w-5 h-5 shrink-0 mt-0.5 ${g.severity === 'critical' ? 'text-red-400' : g.severity === 'major' ? 'text-orange-400' : 'text-blue-400'}`} />
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge label={g.severity} variant={g.severity as any} />
                    <Badge label={g.status} variant={g.status === 'open' ? 'warning' : 'success'} />
                    <span className="text-blue-400 text-xs font-mono">{g.regulation} · {g.clause}</span>
                  </div>
                  <p className="text-white font-semibold text-sm mt-2">{g.gap_description}</p>
                  <div className="mt-3 space-y-2 text-xs text-gray-400">
                    <div>
                      <span className="text-gray-500">Requirement: </span>
                      {g.requirement}
                    </div>
                    <div>
                      <span className="text-gray-500">Current state: </span>
                      {g.current_state}
                    </div>
                    <div className="bg-gray-800 rounded-lg p-2 mt-2">
                      <span className="text-green-400 font-medium">→ Corrective Action: </span>
                      {g.corrective_action}
                    </div>
                    <div className="flex gap-4">
                      <span>Area: {g.area}</span>
                      <span>Due: <span className="text-orange-400">{g.due_date}</span></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Health dashboard */}
      {tab === 'health' && health && (
        <div className="space-y-5">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-2">Overall Compliance Score</h3>
            <div className="flex items-end gap-4">
              <span className={`text-5xl font-bold ${health.overall_score >= 80 ? 'text-green-400' : health.overall_score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                {health.overall_score}%
              </span>
              <div className="text-sm text-gray-400 pb-1">
                <p>{health.summary?.critical} critical · {health.summary?.major} major · {health.summary?.minor} minor open gaps</p>
              </div>
            </div>
            <div className="h-2 bg-gray-700 rounded-full mt-3">
              <div
                className={`h-2 rounded-full ${health.overall_score >= 80 ? 'bg-green-500' : health.overall_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${health.overall_score}%` }}
              />
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {Object.entries(health.by_regulation ?? {}).map(([reg, data]: [string, any]) => (
              <div key={reg} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-white font-medium text-sm">{reg}</span>
                  <span className={`text-lg font-bold ${data.score >= 80 ? 'text-green-400' : data.score >= 60 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {data.score}%
                  </span>
                </div>
                <div className="h-1.5 bg-gray-700 rounded-full mb-2">
                  <div
                    className={`h-1.5 rounded-full ${data.score >= 80 ? 'bg-green-500' : data.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                    style={{ width: `${data.score}%` }}
                  />
                </div>
                <div className="flex gap-3 text-xs">
                  {data.critical > 0 && <span className="text-red-400">{data.critical} critical</span>}
                  {data.major > 0 && <span className="text-orange-400">{data.major} major</span>}
                  <span className="text-gray-500">{data.open_gaps} total open</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit Package */}
      {tab === 'audit' && (
        <div className="space-y-5">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
            <h3 className="text-white font-semibold">Generate Audit Evidence Package</h3>
            <p className="text-gray-400 text-sm">Select a regulation to auto-generate a structured compliance evidence package for audit preparation.</p>
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <label className="text-xs text-gray-400 mb-1 block">Regulation</label>
                <select
                  value={auditReg}
                  onChange={e => setAuditReg(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 outline-none"
                >
                  {REGULATIONS.map(r => <option key={r}>{r}</option>)}
                </select>
              </div>
              <button
                onClick={() => auditMutation.mutate()}
                disabled={auditMutation.isPending}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
              >
                {auditMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
                Generate
              </button>
            </div>
          </div>

          {auditResult && (
            <div className="bg-gray-900 border border-blue-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <ShieldCheck className="w-5 h-5 text-blue-400" />
                <h3 className="text-white font-semibold">Audit Package — {auditResult.regulation}</h3>
                <Badge label={`${auditResult.critical_gaps} critical gaps`} variant="critical" />
              </div>
              <pre className="whitespace-pre-wrap font-sans text-sm text-gray-300 leading-relaxed">{auditResult.package_content}</pre>
              <p className="text-xs text-gray-500 mt-4">Generated: {new Date(auditResult.generated_at).toLocaleString()}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
