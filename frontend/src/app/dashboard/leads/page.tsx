'use client'

import { useState, useEffect } from 'react'
import { leadsApi } from '@/lib/api'

interface Lead {
  lead_id: number
  client_name: string
  job_title: string
  state: string
  posting_date: string
  source: string
  lead_status: string
  contact_email: string
  salary_min: number
  salary_max: number
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 10

  useEffect(() => {
    fetchLeads()
  }, [page])

  const fetchLeads = async () => {
    try {
      setLoading(true)
      const response = await leadsApi.list({ page, limit: pageSize })
      setLeads(response.items || [])
      setTotal(response.total || 0)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch leads')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      new: 'bg-blue-100 text-blue-800',
      enriched: 'bg-yellow-100 text-yellow-800',
      validated: 'bg-green-100 text-green-800',
      sent: 'bg-purple-100 text-purple-800',
      skipped: 'bg-gray-100 text-gray-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading leads...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Leads</h1>
        <button className="btn-primary">
          + Add Lead
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      <div className="card overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Client / Job
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Location
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Source
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Salary Range
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {leads.map((lead) => (
              <tr key={lead.lead_id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-gray-900">{lead.client_name}</div>
                  <div className="text-sm text-gray-500">{lead.job_title}</div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {lead.state || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {lead.source || '-'}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(lead.lead_status)}`}>
                    {lead.lead_status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {lead.contact_email || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {lead.salary_min && lead.salary_max
                    ? `$${lead.salary_min.toLocaleString()} - $${lead.salary_max.toLocaleString()}`
                    : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {leads.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No leads found
          </div>
        )}

        {/* Pagination */}
        <div className="bg-gray-50 px-6 py-3 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} results
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border rounded text-sm disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * pageSize >= total}
              className="px-3 py-1 border rounded text-sm disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
