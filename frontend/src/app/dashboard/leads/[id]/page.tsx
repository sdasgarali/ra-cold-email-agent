'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { leadsApi, api } from '@/lib/api'

interface Contact {
  contact_id: number
  first_name: string
  last_name: string
  email: string
  title: string
  priority_level: string
  validation_status: string
  source: string
}

interface OutreachEvent {
  event_id: number
  contact_id: number
  sent_at: string
  channel: string
  subject: string
  status: string
  bounce_reason: string
  reply_detected_at: string
  body_html: string
  body_text: string
  reply_subject: string
  reply_body: string
}

interface LeadDetail {
  lead_id: number
  client_name: string
  job_title: string
  state: string
  posting_date: string
  job_link: string
  salary_min: number
  salary_max: number
  source: string
  lead_status: string
  ra_name: string
  first_name: string
  last_name: string
  contact_email: string
  contact_phone: string
  contact_count: number
  created_at: string
  updated_at: string
  contacts: Contact[]
  outreach_events: OutreachEvent[]
}

const STATUS_COLORS: Record<string, string> = {
  new: 'bg-slate-100 text-slate-800',
  enriched: 'bg-purple-100 text-purple-800',
  validated: 'bg-teal-100 text-teal-800',
  open: 'bg-green-100 text-green-800',
  hunting: 'bg-yellow-100 text-yellow-800',
  sent: 'bg-indigo-100 text-indigo-800',
  skipped: 'bg-orange-100 text-orange-800',
  closed_hired: 'bg-blue-100 text-blue-800',
  closed_not_hired: 'bg-gray-100 text-gray-800',
}

export default function LeadDetailPage() {
  const params = useParams()
  const router = useRouter()
  const leadId = Number(params.id)

  const [lead, setLead] = useState<LeadDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [expandedEvent, setExpandedEvent] = useState<number | null>(null)
  const [sendingOutreach, setSendingOutreach] = useState(false)
  const [dryRun, setDryRun] = useState(true)
  const [removingContact, setRemovingContact] = useState<number | null>(null)

  useEffect(() => {
    if (leadId) fetchLeadDetail()
  }, [leadId])

  const fetchLeadDetail = async () => {
    try {
      setLoading(true)
      const data = await leadsApi.getDetail(leadId)
      setLead(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch lead details')
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveContact = async (contactId: number) => {
    try {
      setRemovingContact(contactId)
      await leadsApi.manageContacts(leadId, { remove_contact_ids: [contactId] })
      setSuccess('Contact removed from this lead')
      fetchLeadDetail()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove contact')
    } finally {
      setRemovingContact(null)
    }
  }

  const handleSendOutreach = async () => {
    try {
      setSendingOutreach(true)
      const result = await leadsApi.runOutreach(leadId, dryRun)
      if (dryRun) {
        setSuccess('Dry run complete: ' + (result.message || JSON.stringify(result)))
      } else {
        setSuccess('Outreach sent successfully!')
        fetchLeadDetail()
      }
      setTimeout(() => setSuccess(''), 5000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send outreach')
    } finally {
      setSendingOutreach(false)
    }
  }

  const formatDate = (d: string | null) => {
    if (!d) return '-'
    try { return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) }
    catch { return d }
  }

  const formatDateTime = (d: string | null) => {
    if (!d) return '-'
    try { return new Date(d).toLocaleString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) }
    catch { return d }
  }

  const formatSalary = (min: number | null, max: number | null) => {
    if (!min && !max) return '-'
    const fmt = (v: number) => '$' + v.toLocaleString()
    if (min && max) return fmt(min) + ' - ' + fmt(max)
    if (min) return fmt(min) + '+'
    return 'Up to ' + fmt(max!)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-gray-500">Loading lead details...</div>
      </div>
    )
  }

  if (error && !lead) {
    return (
      <div className="max-w-4xl mx-auto py-8">
        <div className="bg-red-50 text-red-600 px-4 py-3 rounded-lg mb-4">{error}</div>
        <button onClick={() => router.push('/dashboard/leads')} className="btn-secondary">Back to Leads</button>
      </div>
    )
  }

  if (!lead) return null

  return (
    <div className="max-w-6xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
        <Link href="/dashboard/leads" className="hover:text-blue-600">Leads</Link>
        <span>/</span>
        <span className="text-gray-800 font-medium">#{lead.lead_id} - {lead.client_name}</span>
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4 flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError('')} className="font-bold">x</button>
        </div>
      )}
      {success && (
        <div className="bg-green-50 text-green-600 px-4 py-2 rounded-lg mb-4">{success}</div>
      )}

      {/* Lead Info Card */}
      <div className="card p-6 mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">{lead.client_name}</h1>
            <p className="text-lg text-gray-600 mt-1">{lead.job_title}</p>
          </div>
          <span className={'px-3 py-1 rounded-full text-sm font-medium ' + (STATUS_COLORS[lead.lead_status] || 'bg-gray-100 text-gray-800')}>
            {lead.lead_status}
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">State:</span>
            <span className="ml-2 font-medium">{lead.state || '-'}</span>
          </div>
          <div>
            <span className="text-gray-500">Posted:</span>
            <span className="ml-2 font-medium">{formatDate(lead.posting_date)}</span>
          </div>
          <div>
            <span className="text-gray-500">Salary:</span>
            <span className="ml-2 font-medium">{formatSalary(lead.salary_min, lead.salary_max)}</span>
          </div>
          <div>
            <span className="text-gray-500">Source:</span>
            <span className="ml-2"><span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{lead.source}</span></span>
          </div>
          <div>
            <span className="text-gray-500">Created:</span>
            <span className="ml-2 font-medium">{formatDate(lead.created_at)}</span>
          </div>
          <div>
            <span className="text-gray-500">Updated:</span>
            <span className="ml-2 font-medium">{formatDate(lead.updated_at)}</span>
          </div>
          {lead.job_link && (
            <div className="col-span-2">
              <span className="text-gray-500">Job Link:</span>
              <a href={lead.job_link} target="_blank" rel="noopener noreferrer" className="ml-2 text-blue-600 hover:underline">View Posting</a>
            </div>
          )}
        </div>
      </div>

      {/* Contacts Section */}
      <div className="card mb-6">
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-800">
            Contacts ({lead.contacts.length})
          </h2>
        </div>
        {lead.contacts.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">
            No contacts linked to this lead. Run Contact Enrichment to discover contacts.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Validation</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {lead.contacts.map((c) => (
                  <tr key={c.contact_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="text-sm font-medium text-gray-900">{c.first_name} {c.last_name}</div>
                      <div className="text-xs text-gray-500">{c.title || '-'}</div>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <a href={'mailto:' + c.email} className="text-blue-600 hover:underline">{c.email}</a>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700">
                        {c.priority_level ? c.priority_level.split('_')[0].toUpperCase() : '-'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={'text-xs px-2 py-1 rounded-full ' + (
                        c.validation_status === 'valid' ? 'bg-green-100 text-green-800' :
                        c.validation_status === 'invalid' ? 'bg-red-100 text-red-800' :
                        'bg-gray-100 text-gray-600'
                      )}>
                        {c.validation_status || 'pending'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">{c.source || '-'}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleRemoveContact(c.contact_id)}
                        disabled={removingContact === c.contact_id}
                        className="text-xs text-red-600 hover:text-red-800 disabled:opacity-50"
                      >
                        {removingContact === c.contact_id ? 'Removing...' : 'Remove'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Outreach Section */}
      <div className="card mb-6">
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-800">
            Outreach ({lead.outreach_events.length} events)
          </h2>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={dryRun}
                onChange={(e) => setDryRun(e.target.checked)}
                className="w-4 h-4"
              />
              Dry Run
            </label>
            <button
              onClick={handleSendOutreach}
              disabled={sendingOutreach || lead.contacts.length === 0}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 text-sm font-medium"
            >
              {sendingOutreach ? 'Sending...' : 'Send Outreach'}
            </button>
          </div>
        </div>
        {lead.outreach_events.length === 0 ? (
          <div className="px-6 py-8 text-center text-gray-500">
            No outreach events yet. Click "Send Outreach" to email contacts linked to this lead.
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {lead.outreach_events.map((evt) => (
              <div key={evt.event_id}>
                <div
                  onClick={() => setExpandedEvent(expandedEvent === evt.event_id ? null : evt.event_id)}
                  className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-gray-50"
                >
                  <div className="flex items-center gap-4">
                    <span className={'text-xs px-2 py-1 rounded-full ' + (
                      evt.status === 'sent' ? 'bg-green-100 text-green-800' :
                      evt.status === 'bounced' ? 'bg-red-100 text-red-800' :
                      evt.status === 'replied' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-700'
                    )}>
                      {evt.status}
                    </span>
                    <div>
                      <div className="text-sm font-medium text-gray-900">{evt.subject || '(no subject)'}</div>
                      <div className="text-xs text-gray-500">
                        Contact #{evt.contact_id} | {formatDateTime(evt.sent_at)} | {evt.channel}
                      </div>
                    </div>
                  </div>
                  <span className="text-gray-400 text-sm">{expandedEvent === evt.event_id ? '\u25B2' : '\u25BC'}</span>
                </div>
                {expandedEvent === evt.event_id && (
                  <div className="px-6 pb-4">
                    {evt.body_text && (
                      <div className="mb-4">
                        <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">Email Body</h4>
                        <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap">
                          {evt.body_text}
                        </div>
                      </div>
                    )}
                    {evt.body_html && !evt.body_text && (
                      <div className="mb-4">
                        <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">Email Body (HTML)</h4>
                        <div className="bg-gray-50 rounded-lg p-4 text-sm" dangerouslySetInnerHTML={{ __html: evt.body_html }} />
                      </div>
                    )}
                    {evt.reply_body && (
                      <div className="mb-4">
                        <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
                          Reply {evt.reply_subject ? '- ' + evt.reply_subject : ''}
                        </h4>
                        <div className="bg-blue-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap border-l-4 border-blue-300">
                          {evt.reply_body}
                        </div>
                      </div>
                    )}
                    {evt.bounce_reason && (
                      <div className="bg-red-50 rounded-lg p-3 text-sm text-red-700">
                        Bounce reason: {evt.bounce_reason}
                      </div>
                    )}
                    {!evt.body_text && !evt.body_html && !evt.reply_body && !evt.bounce_reason && (
                      <div className="text-sm text-gray-400 italic">No email content stored for this event.</div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
