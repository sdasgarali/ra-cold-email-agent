'use client'

import { useState, useEffect } from 'react'
import { clientsApi } from '@/lib/api'

interface Client {
  client_id: number
  client_name: string
  status: string
  industry: string
  company_size: string
  location_state: string
  client_category: string
  service_count: number
  start_date: string
}

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchClients()
  }, [])

  const fetchClients = async () => {
    try {
      setLoading(true)
      const response = await clientsApi.list({ limit: 50 })
      setClients(response || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch clients')
    } finally {
      setLoading(false)
    }
  }

  const getCategoryBadge = (category: string) => {
    const colors: Record<string, string> = {
      regular: 'bg-green-100 text-green-800',
      occasional: 'bg-blue-100 text-blue-800',
      prospect: 'bg-yellow-100 text-yellow-800',
      dormant: 'bg-gray-100 text-gray-800',
    }
    return colors[category] || 'bg-gray-100 text-gray-800'
  }

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-red-100 text-red-800',
      prospect: 'bg-yellow-100 text-yellow-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading clients...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Clients</h1>
        <button className="btn-primary">
          + Add Client
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
                Client Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Industry
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Size
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Services
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {clients.map((client) => (
              <tr key={client.client_id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-gray-900">{client.client_name}</div>
                  <div className="text-sm text-gray-500">{client.location_state || '-'}</div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {client.industry || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {client.company_size || '-'}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(client.status)}`}>
                    {client.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${getCategoryBadge(client.client_category)}`}>
                    {client.client_category}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {client.service_count || 0}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {clients.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No clients found
          </div>
        )}
      </div>
    </div>
  )
}
