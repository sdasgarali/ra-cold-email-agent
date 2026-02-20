'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { leadsApi, api } from '@/lib/api'

interface Lead {
  lead_id: number
  client_name: string
  job_title: string
  state: string
  posting_date: string
  job_link: string
  source: string
  lead_status: string
  contact_email: string
  salary_min: number
  salary_max: number
  contact_count: number  // Number of contacts linked to this lead
  created_at: string
  updated_at: string
}

interface Contact {
  contact_id: number
  lead_id: number
  first_name: string
  last_name: string
  email: string
  title: string
  validation_status: string
}

const STATUS_OPTIONS = [
  { value: 'new', label: 'New', color: 'bg-slate-100 text-slate-800' },
  { value: 'enriched', label: 'Enriched', color: 'bg-purple-100 text-purple-800' },
  { value: 'validated', label: 'Validated', color: 'bg-teal-100 text-teal-800' },
  { value: 'open', label: 'Open', color: 'bg-green-100 text-green-800' },
  { value: 'hunting', label: 'Hunting', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'sent', label: 'Sent', color: 'bg-indigo-100 text-indigo-800' },
  { value: 'skipped', label: 'Skipped', color: 'bg-orange-100 text-orange-800' },
  { value: 'closed_hired', label: 'Closed-Hired', color: 'bg-blue-100 text-blue-800' },
  { value: 'closed_not_hired', label: 'Closed-Not-Hired', color: 'bg-gray-100 text-gray-800' },
]

const SOURCE_OPTIONS = ['jsearch', 'apollo', 'indeed', 'linkedin', 'glassdoor', 'mock', 'import']

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
]

type SortField = 'client_name' | 'job_title' | 'state' | 'posting_date' | 'created_at' | 'source' | 'lead_status'
type SortOrder = 'asc' | 'desc'

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [updating, setUpdating] = useState<number | null>(null)
  const [pageSize, setPageSize] = useState(25)

  // Filters
  const [showFilters, setShowFilters] = useState(false)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterSource, setFilterSource] = useState('')
  const [filterState, setFilterState] = useState('')
  const [filterFromDate, setFilterFromDate] = useState('')
  const [filterToDate, setFilterToDate] = useState('')

  // Sorting
  const [sortBy, setSortBy] = useState<SortField>('created_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  // Import
  const [importing, setImporting] = useState(false)
  const [exporting, setExporting] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Contacts modal
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const [leadContacts, setLeadContacts] = useState<Contact[]>([])
  const [loadingContacts, setLoadingContacts] = useState(false)

  // Bulk delete
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [deleting, setDeleting] = useState(false)

  // Debounce search
  const [debouncedSearch, setDebouncedSearch] = useState('')
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    fetchLeads()
  }, [page, pageSize, debouncedSearch, filterStatus, filterSource, filterState, filterFromDate, filterToDate, sortBy, sortOrder])

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const params: Record<string, any> = {
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
      }
      if (debouncedSearch) params.search = debouncedSearch
      if (filterStatus) params.status = filterStatus
      if (filterSource) params.source = filterSource
      if (filterState) params.state = filterState
      if (filterFromDate) params.from_date = filterFromDate
      if (filterToDate) params.to_date = filterToDate

      const response = await leadsApi.list(params)
      setLeads(response.items || [])
      setTotal(response.total || 0)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch leads')
    } finally {
      setLoading(false)
    }
  }

  const updateLeadStatus = async (leadId: number, newStatus: string) => {
    try {
      setUpdating(leadId)
      await leadsApi.update(leadId, { lead_status: newStatus })
      setLeads(leads.map(lead =>
        lead.lead_id === leadId ? { ...lead, lead_status: newStatus } : lead
      ))
      setSuccess('Status updated successfully')
      setTimeout(() => setSuccess(''), 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update status')
    } finally {
      setUpdating(null)
    }
  }

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('asc')
    }
    setPage(1)
  }

  const clearFilters = () => {
    setSearch('')
    setFilterStatus('')
    setFilterSource('')
    setFilterState('')
    setFilterFromDate('')
    setFilterToDate('')
    setPage(1)
  }

  const handleExport = async () => {
    try {
      setExporting(true)
      const params = new URLSearchParams()
      if (filterStatus) params.append('status', filterStatus)
      if (filterSource) params.append('source', filterSource)
      if (filterState) params.append('state', filterState)
      if (filterFromDate) params.append('from_date', filterFromDate)
      if (filterToDate) params.append('to_date', filterToDate)
      if (debouncedSearch) params.append('search', debouncedSearch)

      const response = await api.get(`/leads/export/csv?${params.toString()}`, {
        responseType: 'blob'
      })

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `leads_export_${new Date().toISOString().slice(0, 10)}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      setSuccess('Export completed successfully')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to export leads')
    } finally {
      setExporting(false)
    }
  }

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setImporting(true)
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/leads/import/csv', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      const result = response.data
      setSuccess(`Import complete: ${result.imported} leads imported, ${result.skipped} skipped`)
      if (result.errors?.length > 0) {
        setError(`Errors: ${result.errors.join(', ')}`)
      }
      fetchLeads()
      setTimeout(() => setSuccess(''), 5000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import leads')
    } finally {
      setImporting(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const fetchContactsForLead = async (lead: Lead) => {
    try {
      setSelectedLead(lead)
      setLoadingContacts(true)
      const response = await api.get(`/contacts?lead_id=${lead.lead_id}`)
      setLeadContacts(response.data.items || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch contacts')
    } finally {
      setLoadingContacts(false)
    }
  }

  const closeContactsModal = () => {
    setSelectedLead(null)
    setLeadContacts([])
  }

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const toggleSelectAll = () => {
    if (selectedIds.size === leads.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(leads.map(l => l.lead_id)))
    }
  }

  const handleBulkDelete = async () => {
    try {
      setDeleting(true)
      await api.delete('/leads/bulk', { data: { lead_ids: Array.from(selectedIds) } })
      setSuccess(`Successfully deleted ${selectedIds.size} lead(s) and their linked contacts`)
      setSelectedIds(new Set())
      setShowDeleteModal(false)
      fetchLeads()
      setTimeout(() => setSuccess(''), 4000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete leads')
    } finally {
      setDeleting(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const statusOption = STATUS_OPTIONS.find(s => s.value === status)
    return statusOption?.color || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    } catch {
      return dateString
    }
  }

  const truncateUrl = (url: string | null, maxLength: number = 30) => {
    if (!url) return '-'
    if (url.length <= maxLength) return url
    return url.substring(0, maxLength) + '...'
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortBy !== field) return <span className="text-gray-300 ml-1">&#8645;</span>
    return sortOrder === 'asc' ? <span className="ml-1">&#8593;</span> : <span className="ml-1">&#8595;</span>
  }

  const activeFiltersCount = [filterStatus, filterSource, filterState, filterFromDate, filterToDate, search].filter(Boolean).length

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Leads</h1>
          <p className="text-gray-500 text-sm mt-1">
            {total} job postings sourced from LinkedIn, Indeed, Glassdoor, and more
          </p>
        </div>
        <div className="flex gap-2">
          {selectedIds.size > 0 && (
            <button
              onClick={() => setShowDeleteModal(true)}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex items-center gap-2 text-sm font-medium"
            >
              Delete Selected ({selectedIds.size})
            </button>
          )}
          {/* Import Button */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImport}
            accept=".csv"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={importing}
            className="btn-secondary flex items-center gap-2"
          >
            {importing ? (
              <>
                <span className="animate-spin">&#8635;</span>
                Importing...
              </>
            ) : (
              <>
                <span>&#8593;</span>
                Import CSV
              </>
            )}
          </button>

          {/* Export Button */}
          <button
            onClick={handleExport}
            disabled={exporting}
            className="btn-secondary flex items-center gap-2"
          >
            {exporting ? (
              <>
                <span className="animate-spin">&#8635;</span>
                Exporting...
              </>
            ) : (
              <>
                <span>&#8595;</span>
                Export CSV
              </>
            )}
          </button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4 flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="font-bold">x</button>
        </div>
      )}
      {success && (
        <div className="bg-green-50 text-green-600 px-4 py-2 rounded-lg mb-4">
          {success}
        </div>
      )}

      {/* Search and Filter Bar */}
      <div className="card p-4 mb-4">
        <div className="flex flex-wrap gap-4 items-center">
          {/* Search */}
          <div className="flex-1 min-w-64">
            <input
              type="text"
              placeholder="Search company, job title, or state..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="input w-full"
            />
          </div>

          {/* Quick Filters */}
          <select
            value={filterStatus}
            onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
            className="input w-40"
          >
            <option value="">All Statuses</option>
            {STATUS_OPTIONS.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>

          <select
            value={filterSource}
            onChange={(e) => { setFilterSource(e.target.value); setPage(1); }}
            className="input w-36"
          >
            <option value="">All Sources</option>
            {SOURCE_OPTIONS.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          {/* Toggle More Filters */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary text-sm ${activeFiltersCount > 0 ? 'bg-blue-50 border-blue-300' : ''}`}
          >
            Filters {activeFiltersCount > 0 && `(${activeFiltersCount})`}
          </button>

          {activeFiltersCount > 0 && (
            <button onClick={clearFilters} className="text-sm text-gray-500 hover:text-gray-700">
              Clear all
            </button>
          )}
        </div>

        {/* Expanded Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t grid grid-cols-4 gap-4">
            <div>
              <label className="label text-sm">State</label>
              <select
                value={filterState}
                onChange={(e) => { setFilterState(e.target.value); setPage(1); }}
                className="input w-full"
              >
                <option value="">All States</option>
                {US_STATES.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label text-sm">Posted From</label>
              <input
                type="date"
                value={filterFromDate}
                onChange={(e) => { setFilterFromDate(e.target.value); setPage(1); }}
                className="input w-full"
              />
            </div>
            <div>
              <label className="label text-sm">Posted To</label>
              <input
                type="date"
                value={filterToDate}
                onChange={(e) => { setFilterToDate(e.target.value); setPage(1); }}
                className="input w-full"
              />
            </div>
            <div>
              <label className="label text-sm">Page Size</label>
              <select
                value={pageSize}
                onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
                className="input w-full"
              >
                <option value="10">10 per page</option>
                <option value="25">25 per page</option>
                <option value="50">50 per page</option>
                <option value="100">100 per page</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Selection Info Bar */}
      {selectedIds.size > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2 mb-4 flex items-center justify-between">
          <span className="text-sm text-blue-800 font-medium">{selectedIds.size} lead(s) selected</span>
          <button onClick={() => setSelectedIds(new Set())} className="text-sm text-blue-600 hover:text-blue-800">Clear selection</button>
        </div>
      )}

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-3 w-10">
                  <input
                    type="checkbox"
                    checked={leads.length > 0 && selectedIds.size === leads.length}
                    onChange={toggleSelectAll}
                    className="w-4 h-4"
                  />
                </th>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th
                  onClick={() => handleSort('client_name')}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  Company / Job Title <SortIcon field="client_name" />
                </th>
                <th
                  onClick={() => handleSort('state')}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  State <SortIcon field="state" />
                </th>
                <th
                  onClick={() => handleSort('posting_date')}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  Posted <SortIcon field="posting_date" />
                </th>
                <th
                  onClick={() => handleSort('source')}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  Source <SortIcon field="source" />
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Link
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contacts
                </th>
                <th
                  onClick={() => handleSort('lead_status')}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                >
                  Status <SortIcon field="lead_status" />
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                    Loading leads...
                  </td>
                </tr>
              ) : leads.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                    No leads found. {activeFiltersCount > 0 ? 'Try adjusting your filters.' : 'Run the Lead Sourcing pipeline to fetch jobs.'}
                  </td>
                </tr>
              ) : (
                leads.map((lead) => (
                  <tr key={lead.lead_id} className={selectedIds.has(lead.lead_id) ? "bg-blue-50 hover:bg-blue-100" : "hover:bg-gray-50"}>
                    <td className="px-3 py-3">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(lead.lead_id)}
                        onChange={() => toggleSelect(lead.lead_id)}
                        className="w-4 h-4"
                      />
                    </td>
                    <td className="px-3 py-3">
                      <Link href={`/dashboard/leads/${lead.lead_id}`} className="text-xs px-2 py-1 rounded bg-blue-50 text-blue-700 font-mono hover:bg-blue-100">
                        #{lead.lead_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/dashboard/leads/${lead.lead_id}`} className="text-sm font-medium text-blue-700 hover:text-blue-900 hover:underline">
                        {lead.client_name}
                      </Link>
                      <div className="text-sm text-gray-500">{lead.job_title}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {lead.state || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDate(lead.posting_date)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
                        {lead.source}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {lead.job_link ? (
                        <a
                          href={lead.job_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 hover:underline"
                          title={lead.job_link}
                        >
                          {truncateUrl(lead.job_link, 25)}
                        </a>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => fetchContactsForLead(lead)}
                        className={`text-xs px-2 py-1 rounded-full ${
                          lead.contact_count > 0
                            ? 'bg-purple-100 text-purple-800 hover:bg-purple-200'
                            : 'bg-gray-100 text-gray-500'
                        }`}
                      >
                        {lead.contact_count || 0} contacts
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <select
                        value={lead.lead_status}
                        onChange={(e) => updateLeadStatus(lead.lead_id, e.target.value)}
                        disabled={updating === lead.lead_id}
                        className={`text-xs px-2 py-1 rounded-full border-0 cursor-pointer ${getStatusBadge(lead.lead_status)} ${updating === lead.lead_id ? 'opacity-50' : ''}`}
                      >
                        {STATUS_OPTIONS.map((status) => (
                          <option key={status.value} value={status.value}>
                            {status.label}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="bg-gray-50 px-6 py-3 flex items-center justify-between border-t">
          <div className="text-sm text-gray-500">
            Showing {leads.length > 0 ? ((page - 1) * pageSize) + 1 : 0} to {Math.min(page * pageSize, total)} of {total} results
          </div>
          <div className="flex gap-2 items-center">
            <button
              onClick={() => setPage(1)}
              disabled={page === 1}
              className="px-2 py-1 border rounded text-sm disabled:opacity-50 hover:bg-gray-100"
              title="First page"
            >
              &laquo;
            </button>
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border rounded text-sm disabled:opacity-50 hover:bg-gray-100"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm text-gray-600">
              Page {page} of {Math.ceil(total / pageSize) || 1}
            </span>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * pageSize >= total}
              className="px-3 py-1 border rounded text-sm disabled:opacity-50 hover:bg-gray-100"
            >
              Next
            </button>
            <button
              onClick={() => setPage(Math.ceil(total / pageSize))}
              disabled={page * pageSize >= total}
              className="px-2 py-1 border rounded text-sm disabled:opacity-50 hover:bg-gray-100"
              title="Last page"
            >
              &raquo;
            </button>
          </div>
        </div>
      </div>

      {/* Import Help */}
      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Import CSV Format:</h4>
        <p className="text-xs text-gray-500 mb-2">
          Required columns: <span className="font-mono bg-gray-200 px-1">Company Name</span>, <span className="font-mono bg-gray-200 px-1">Job Title</span>
        </p>
        <p className="text-xs text-gray-500">
          Optional: <span className="font-mono bg-gray-200 px-1">State</span>, <span className="font-mono bg-gray-200 px-1">Posting Date</span> (YYYY-MM-DD), <span className="font-mono bg-gray-200 px-1">Job Link</span>, <span className="font-mono bg-gray-200 px-1">Source</span>, <span className="font-mono bg-gray-200 px-1">Status</span> (open/hunting/closed_hired/closed_not_hired), <span className="font-mono bg-gray-200 px-1">Salary Min</span>, <span className="font-mono bg-gray-200 px-1">Salary Max</span>
        </p>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b">
              <h3 className="text-lg font-semibold text-red-600">Confirm Bulk Delete</h3>
            </div>
            <div className="px-6 py-4">
              <p className="text-gray-700 mb-3">
                Are you sure you want to delete <strong>{selectedIds.size}</strong> lead(s)?
              </p>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                <p className="font-medium mb-1">This action cannot be undone. It will also delete:</p>
                <ul className="list-disc ml-4 space-y-1">
                  <li>All contacts linked to these leads</li>
                  <li>Related outreach events</li>
                  <li>Related email validation results</li>
                </ul>
              </div>
            </div>
            <div className="px-6 py-4 border-t bg-gray-50 flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                disabled={deleting}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={deleting}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? 'Deleting...' : 'Delete Permanently'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Contacts Modal */}
      {selectedLead && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="px-6 py-4 border-b flex justify-between items-center">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Contacts for {selectedLead.client_name}
                </h3>
                <p className="text-sm text-gray-500">{selectedLead.job_title}</p>
              </div>
              <button
                onClick={closeContactsModal}
                className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
              >
                &times;
              </button>
            </div>

            {/* Modal Body */}
            <div className="px-6 py-4 overflow-y-auto flex-1">
              {loadingContacts ? (
                <div className="text-center py-8 text-gray-500">
                  Loading contacts...
                </div>
              ) : leadContacts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="mb-2">No contacts found for this lead.</p>
                  <p className="text-sm">Run the Contact Enrichment pipeline to discover contacts.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {leadContacts.map((contact) => (
                    <div
                      key={contact.contact_id}
                      className="p-4 border rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-medium text-gray-900">
                            {contact.first_name} {contact.last_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {contact.title || 'No title'}
                          </div>
                          <a
                            href={`mailto:${contact.email}`}
                            className="text-sm text-blue-600 hover:underline"
                          >
                            {contact.email}
                          </a>
                        </div>
                        <div>
                          <span
                            className={`text-xs px-2 py-1 rounded-full ${
                              contact.validation_status === 'valid'
                                ? 'bg-green-100 text-green-800'
                                : contact.validation_status === 'invalid'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {contact.validation_status || 'Not validated'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-4 border-t bg-gray-50 flex justify-between items-center">
              <span className="text-sm text-gray-500">
                {leadContacts.length} contact{leadContacts.length !== 1 ? 's' : ''} linked to this lead
              </span>
              <button
                onClick={closeContactsModal}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
