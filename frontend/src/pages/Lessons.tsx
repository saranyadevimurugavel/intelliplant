import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getLessons, getWarnings, analyzePatterns } from '../api/client'
import { BookOpen, AlertTriangle, TrendingUp, Loader2 } from 'lucide-react'
import Badge from '../components/Badge'

export default function Lessons() {
  const [tab, setTab] = useState<'lessons' | 'warnings' | 'patterns'>('lessons')
  const [patternResult, setPatternResult] = useState<any>(null)
  const [typeFilter, setTypeFilter] = useState('')

  const { data: lessons = [] } = useQuery({
    queryKey: ['lessons', typeFilter],
    queryFn: () => getLessons(typeFilter ? { incident_type: typeFilter } : undefined).then(r => r.data),
  })
  const { data: warnings = [] } = useQuery({ queryKey: ['warnings'], queryFn: () => getWarnings().then(r => r.data) })

  const patternsMutation = useMutation({
    mutationFn: () => analyzePatterns().then(r => r.data),
    onSuccess: setPatternResult,
  })

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Lessons Learned & Failure Intelligence</h1>
        <p className="text-gray-400 text-sm mt-1">Incident history, proactive warnings, and AI pattern analysis</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1">
        {(['lessons', 'warnings', 'patterns'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${tab === t ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-gray-200'}`}
          >
            {t === 'lessons' ? 'Lessons Library' : t === 'warnings' ? `Proactive Warnings${(warnings as any[]).length > 0 ? ` (${(warnings as any[]).length})` : ''}` : 'Pattern Analysis'}
          </button>
        ))}
      </div>

      {/* Lessons Library */}
      {tab === 'lessons' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            {['', 'mechanical_failure', 'near_miss', 'quality_deviation', 'safety'].map(t => (
              <button
                key={t}
                onClick={() => setTypeFilter(t)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${typeFilter === t ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-gray-200'}`}
              >
                {t ? t.replace('_', ' ') : 'All'}
              </button>
            ))}
          </div>

          {(lessons as any[]).map(l => (
            <div key={l.id} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge label={l.severity} variant={l.severity as any} />
                    <Badge label={l.incident_type.replace('_', ' ')} variant="info" />
                    <span className="text-blue-400 font-mono text-xs">{l.asset_tag}</span>
                    {l.recurrence_count > 1 && <Badge label={`${l.recurrence_count}x recurrence`} variant="warning" />}
                  </div>
                  <p className="text-white font-semibold text-sm mt-2">{l.title}</p>
                  <p className="text-gray-400 text-xs mt-1">{l.description}</p>

                  <div className="mt-3 grid md:grid-cols-2 gap-3 text-xs">
                    <div className="bg-gray-800 rounded-lg p-3">
                      <p className="text-red-400 font-medium mb-1">Root Cause</p>
                      <p className="text-gray-400">{l.root_cause}</p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-3">
                      <p className="text-green-400 font-medium mb-1">Preventive Actions</p>
                      <p className="text-gray-400">{l.preventive_actions}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {l.pattern_tags?.map((t: string) => (
                      <span key={t} className="text-xs bg-gray-800 text-purple-300 px-1.5 py-0.5 rounded">{t}</span>
                    ))}
                  </div>
                  <p className="text-gray-600 text-xs mt-2">{l.date} · {l.area}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Proactive Warnings */}
      {tab === 'warnings' && (
        <div className="space-y-4">
          {(warnings as any[]).length === 0 ? (
            <div className="text-center py-12 text-gray-500">No active warnings.</div>
          ) : (
            (warnings as any[]).map(w => (
              <div key={w.id} className={`bg-gray-900 border rounded-xl p-5 ${w.severity === 'critical' ? 'border-red-700' : 'border-orange-700'}`}>
                <div className="flex gap-3">
                  <AlertTriangle className={`w-5 h-5 shrink-0 mt-0.5 ${w.severity === 'critical' ? 'text-red-400' : 'text-orange-400'}`} />
                  <div>
                    <p className="text-white font-semibold">{w.warning_title}</p>
                    <p className="text-gray-400 text-sm mt-1">{w.warning_detail}</p>
                    <div className="bg-gray-800 rounded-lg p-3 mt-3 text-xs">
                      <p className="text-green-400 font-medium">Recommended Action:</p>
                      <p className="text-gray-300 mt-1">{w.recommended_action}</p>
                    </div>
                    <div className="flex gap-3 mt-2 text-xs text-gray-500">
                      <span>Asset: {w.asset_tag}</span>
                      <span>Based on: {w.related_lesson}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Pattern Analysis */}
      {tab === 'patterns' && (
        <div className="space-y-5">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-semibold mb-2">AI Pattern Analysis</h3>
            <p className="text-gray-400 text-sm">Analyse all lessons learned records to identify systemic failure patterns invisible to individual review.</p>
            <button
              onClick={() => patternsMutation.mutate()}
              disabled={patternsMutation.isPending}
              className="mt-4 flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
            >
              {patternsMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <TrendingUp className="w-4 h-4" />}
              {patternsMutation.isPending ? 'Analysing patterns...' : 'Run Pattern Analysis'}
            </button>
          </div>

          {patternResult && (
            <div className="bg-gray-900 border border-blue-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-5 h-5 text-blue-400" />
                <h3 className="text-white font-semibold">Pattern Analysis Results</h3>
                <span className="text-xs text-gray-500">{patternResult.lessons_analyzed} records analysed</span>
              </div>
              <pre className="whitespace-pre-wrap font-sans text-sm text-gray-300 leading-relaxed">{patternResult.pattern_analysis}</pre>
              <p className="text-xs text-gray-500 mt-4">Generated: {new Date(patternResult.generated_at).toLocaleString()}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
