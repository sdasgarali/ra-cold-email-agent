'use client'

import { useState, useEffect } from 'react'
import { contactsApi } from '@/lib/api'

interface Contact {
  contact_id: number
  client_name: string
  first_name: string
  last_name: string
  title: string
  email: string
  phone: string
  location_state: string
  priority_level: string
  validation_status: string
  source: string
}

export default function ContactsPage() {
  const [contacts, setContacts] = useState<Contact[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const pageSize = 10

  useEffect(() => {
    fetchContacts()
  }, [page])

  const fetchContacts = async () => {
    try {
      setLoading(true)
      const response = await contactsApi.list({ page, limit: pageSize })
      setContacts(response || [])
      setTotal(response?.length || 0)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch contacts')
    } finally {
      setLoading(false)
    }
  }

  const getValidationBadge = (status: string) => {
    const colors: Record<string, string> = {
      valid: 'bg-green-100 text-green-800',
      invalid: 'bg-red-100 text-red-800',
      unknown: 'bg-gray-100 text-gray-800',
      pending: 'bg-yellow-100 text-yellow-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getPriorityBadge = (priority: string) => {
    if (!priority) return 'bg-gray-100 text-gray-800'
    const level = priority.split('_')[0]
    const colors: Record<string, string> = {
      p1: 'bg-red-100 text-red-800',
      p2: 'bg-orange-100 text-orange-800',
      p3: 'bg-yellow-100 text-yellow-800',
      p4: 'bg-blue-100 text-blue-800',
      p5: 'bg-gray-100 text-gray-800',
    }
    return colors[level] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading contacts...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Contacts</h1>
        <button className="btn-primary">
          + Add Contact
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
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Priority
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Validation
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Source
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {contacts.map((contact) => (
              <tr key={contact.contact_id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="text-sm font-medium text-gray-900">
                    {contact.first_name} {contact.last_name}
                  </div>
                  <div className="text-sm text-gray-500">{contact.title || '-'}</div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {contact.client_name || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {contact.email || '-'}
                </td>
                <td className="px-6 py-4">
                  {contact.priority_level ? (
                    <span className={`px-2 py-1 text-xs rounded-full ${getPriorityBadge(contact.priority_level)}`}>
                      {contact.priority_level.split('_')[0].toUpperCase()}
                    </span>
                  ) : '-'}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${getValidationBadge(contact.validation_status || 'unknown')}`}>
                    {contact.validation_status || 'unknown'}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {contact.source || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {contacts.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No contacts found
          </div>
        )}
      </div>
    </div>
  )
}
