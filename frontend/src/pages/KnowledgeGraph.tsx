import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getKGStats, searchKG, getEntity } from '../api/client'
import { Activity, Search, ChevronRight } from 'lucide-react'
import Badge from '../components/Badge'

export default function KnowledgeGraph() {
  const [query, setQuery] = useState('')
  const [nodeType, setNodeType] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [selected, setSelected] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const { data: stats } = useQuery({ queryKey: ['kg-stats'], queryFn: () => getKGStats().then(r => r.data) })

  const search = async () => {
    if (!query) return
    setLoading(true)
    try {
      const res = await searchKG(query, nodeType || undefined)
      setResults(res.data.results)
    } finally {
      setLoading(false)
    }
  }

  const selectEntity = async (id: string) => {
    const res = await getEntity(id)
    setSelected(res.data)
  }

  const nodeTypeColor: Record<string, string> = {
    asset: 'bg-blue-900 text-blue-300',
    document: 'bg-purple-900 text-purple-300',
    work_order: 'bg-orange-900 text-orange-300',
    regulation: 'bg-green-900 text-green-300',
    incident: 'bg-red-900 text-red-300',
    person: 'bg-gray-700 text-gray-300',
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Knowledge Graph Explorer</h1>
        <p className="text-gray-400 text-sm mt-1">Explore entities and relationships across your industrial knowledge base</p>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total Nodes" value={stats.total_nodes} color="blue" />
          <StatCard label="Total Edges" value={stats.total_edges} color="purple" />
          {Object.entries(stats.node_types ?? {}).slice(0, 2).map(([type, count]: [string, any]) => (
            <StatCard key={type} label={`${type.charAt(0).toUpperCase() + type.slice(1)}s`} value={count} color="gray" />
          ))}
        </div>
      )}

      {/* Node type distribution */}
      {stats?.node_types && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-white font-semibold mb-4">Node Distribution</h3>
          <div className="space-y-2">
            {Object.entries(stats.node_types).map(([type, count]: [string, any]) => {
              const total = stats.total_nodes || 1
              return (
                <div key={type} className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded font-medium w-24 text-center ${nodeTypeColor[type] ?? 'bg-gray-700 text-gray-300'}`}>
                    {type}
                  </span>
                  <div className="flex-1 h-2 bg-gray-700 rounded-full">
                    <div
                      className="h-2 bg-blue-500 rounded-full"
                      style={{ width: `${(count / total) * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-400 w-8 text-right">{count}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
        <h3 className="text-white font-semibold">Search Entities</h3>
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && search()}
              placeholder="Search by name, tag, or description..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-9 pr-4 py-2 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-blue-500"
            />
          </div>
          <select
            value={nodeType}
            onChange={e => setNodeType(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-sm text-gray-300 rounded-lg px-3 py-2 outline-none"
          >
            <option value="">All types</option>
            {['asset', 'document', 'work_order', 'regulation', 'incident', 'person'].map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <button
            onClick={search}
            disabled={!query || loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium disabled:opacity-40 transition-colors"
          >
            Search
          </button>
        </div>

        {results.length > 0 && (
          <div className="space-y-2 mt-2">
            {results.map((r: any) => (
              <button
                key={r.node_id}
                onClick={() => selectEntity(r.node_id)}
                className="w-full text-left flex items-center gap-3 bg-gray-800 hover:bg-gray-700 rounded-lg px-4 py-3 transition-colors"
              >
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${nodeTypeColor[r.type] ?? 'bg-gray-700 text-gray-300'}`}>
                  {r.type}
                </span>
                <span className="text-sm text-white">{r.node_id}</span>
                {r.name && <span className="text-xs text-gray-400 truncate">{r.name}</span>}
                <ChevronRight className="w-4 h-4 text-gray-600 ml-auto shrink-0" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Entity detail */}
      {selected && (
        <div className="bg-gray-900 border border-blue-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-blue-400" />
            <h3 className="text-white font-semibold">{selected.entity_id}</h3>
            <Badge label={selected.attributes?.type ?? 'unknown'} variant="info" />
          </div>

          {/* Attributes */}
          <div>
            <p className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wide">Attributes</p>
            <div className="grid md:grid-cols-2 gap-2">
              {Object.entries(selected.attributes ?? {}).filter(([k]) => k !== 'type').map(([k, v]: [string, any]) => (
                <div key={k} className="flex gap-2 text-xs">
                  <span className="text-gray-500 w-32 shrink-0">{k}:</span>
                  <span className="text-gray-300 truncate">{String(v)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Relationships */}
          {selected.neighbors?.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wide">Relationships ({selected.neighbors.length})</p>
              <div className="space-y-1.5">
                {selected.neighbors.map((n: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 bg-gray-800 rounded-lg px-3 py-2">
                    <span className="text-blue-400 text-xs">{selected.entity_id}</span>
                    <span className="text-gray-500 text-xs">—{n.relation}→</span>
                    <button onClick={() => selectEntity(n.node_id)} className="text-xs text-white hover:text-blue-400 font-mono">
                      {n.node_id}
                    </button>
                    <Badge label={n.type ?? 'node'} className="ml-auto" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-950 border-blue-800',
    purple: 'bg-purple-950 border-purple-800',
    gray: 'bg-gray-900 border-gray-800',
  }
  return (
    <div className={`border rounded-xl p-4 ${colors[color] ?? colors.gray}`}>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value.toLocaleString()}</p>
    </div>
  )
}
