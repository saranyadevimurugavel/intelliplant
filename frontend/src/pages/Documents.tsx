import { useState, useRef, type ReactNode } from 'react'
import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listDocuments, uploadDocument } from '../api/client'
import { Upload, FileText, CheckCircle, Clock, AlertCircle, Search, Filter } from 'lucide-react'
import Badge from '../components/Badge'

const CATEGORIES = ['general', 'maintenance', 'operating_procedure', 'safety', 'engineering', 'inspection', 'regulation', 'incident']

export default function Documents() {
  const qc = useQueryClient()
  const [category, setCategory] = useState('general')
  const [filter, setFilter] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const { data: docs = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => listDocuments().then(r => r.data),
    refetchInterval: 5000,
  })

  const upload = useMutation({
    mutationFn: ({ file, cat }: { file: File; cat: string }) => uploadDocument(file, cat),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents'] }),
  })

  const handleFiles = (files: FileList | null) => {
    if (!files) return
    Array.from(files).forEach(file => upload.mutate({ file, cat: category }))
  }

  const filtered = docs.filter((d: any) =>
    !filter || d.filename?.toLowerCase().includes(filter.toLowerCase()) ||
    d.category?.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Document Library</h1>
        <p className="text-gray-400 text-sm mt-1">Upload and manage your industrial document corpus</p>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleFiles(e.dataTransfer.files) }}
        onClick={() => fileRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          dragOver ? 'border-blue-500 bg-blue-950' : 'border-gray-700 bg-gray-900 hover:border-gray-600'
        }`}
      >
        <input ref={fileRef} type="file" className="hidden" multiple accept=".pdf,.docx,.xlsx,.xls,.csv,.jpg,.jpeg,.png,.tiff,.tif,.txt"
          onChange={e => handleFiles(e.target.files)} />
        <Upload className="w-8 h-8 text-gray-500 mx-auto mb-3" />
        <p className="text-gray-300 font-medium">Drop files here or click to upload</p>
        <p className="text-gray-500 text-sm mt-1">PDF, DOCX, Excel, CSV, Images (scanned forms, P&IDs)</p>

        <div className="mt-4 flex items-center gap-2 justify-center">
          <label className="text-xs text-gray-400">Category:</label>
          <select
            value={category}
            onChange={e => { e.stopPropagation(); setCategory(e.target.value) }}
            onClick={e => e.stopPropagation()}
            className="text-xs bg-gray-800 border border-gray-700 text-gray-300 rounded px-2 py-1"
          >
            {CATEGORIES.map(c => <option key={c} value={c}>{c.replace('_', ' ')}</option>)}
          </select>
        </div>
      </div>

      {/* Upload progress */}
      {upload.isPending && (
        <div className="flex items-center gap-2 text-blue-400 text-sm bg-blue-950 border border-blue-800 rounded-lg px-4 py-2">
          <Clock className="w-4 h-4 animate-spin" />
          Uploading and processing documents...
        </div>
      )}

      {/* Search and filter */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
          <input
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Search documents..."
            className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-9 pr-4 py-2 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-blue-500"
          />
        </div>
        <div className="text-xs text-gray-500 flex items-center gap-1">
          <Filter className="w-3.5 h-3.5" />
          {filtered.length} of {docs.length}
        </div>
      </div>

      {/* Document list */}
      {isLoading ? (
        <div className="text-center text-gray-500 py-12">Loading documents...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="w-10 h-10 text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500">No documents yet. Upload some files to get started.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((doc: any) => (
            <DocRow key={doc.id} doc={doc} />
          ))}
        </div>
      )}
    </div>
  )
}

function DocRow({ doc }: { doc: any }) {
  const statusIconMap: Record<string, React.ReactNode> = {
    ready: <CheckCircle className="w-4 h-4 text-green-400" />,
    processing: <Clock className="w-4 h-4 text-yellow-400 animate-spin" />,
    pending: <Clock className="w-4 h-4 text-gray-500" />,
    failed: <AlertCircle className="w-4 h-4 text-red-400" />,
  }
  const statusIcon = statusIconMap[doc.status] ?? <Clock className="w-4 h-4 text-gray-500" />

  return (
    <div className="flex items-start gap-4 bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors">
      <FileText className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-white truncate">{doc.filename}</span>
          <Badge label={doc.category} variant="info" />
          <Badge label={doc.doc_type} />
        </div>
        {doc.summary && <p className="text-xs text-gray-400 mt-1 line-clamp-2">{doc.summary}</p>}
        {doc.entities && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {doc.entities.equipment_tags?.slice(0, 5).map((t: string) => (
              <span key={t} className="text-xs bg-gray-800 text-blue-300 px-1.5 py-0.5 rounded">{t}</span>
            ))}
          </div>
        )}
        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
          {doc.page_count && <span>{doc.page_count} pages</span>}
          {doc.file_size && <span>{Math.round(doc.file_size / 1024)} KB</span>}
          <span>{new Date(doc.created_at).toLocaleDateString()}</span>
        </div>
      </div>
      <div className="flex items-center gap-1 shrink-0">
        {statusIcon}
        <span className="text-xs text-gray-500 capitalize">{doc.status}</span>
      </div>
    </div>
  )
}
