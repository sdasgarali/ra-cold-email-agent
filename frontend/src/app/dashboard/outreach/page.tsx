'use client'

import { useState, useEffect } from 'react'
import { dashboardApi, pipelinesApi, settingsApi } from '@/lib/api'

interface OutreachStats {
  emails_sent: number
  emails_bounced: number
  emails_replied: number
  bounce_rate_percent: number
  reply_rate_percent: number
  total_valid_emails: number
}

interface OutreachEvent {
  contact_name: string
  client_name: string
  email: string
  sent_at: string
  status: string
  channel: string
}

interface Setting {
  key: string
  value_json: string
}

export default function OutreachPage() {
  const [stats, setStats] = useState<OutreachStats | null>(null)
  const [events, setEvents] = useState<OutreachEvent[]>([])
  const [settings, setSettings] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [mode, setMode] = useState<'mailmerge' | 'send'>('mailmerge')
  const [dryRun, setDryRun] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [kpis, outreachData, settingsList] = await Promise.all([
        dashboardApi.kpis(),
        dashboardApi.outreachSent({ limit: 50 }),
        settingsApi.list()
      ])

      setStats({
        emails_sent: kpis.emails_sent || 0,
        emails_bounced: kpis.emails_bounced || 0,
        emails_replied: kpis.emails_replied || 0,
        bounce_rate_percent: kpis.bounce_rate_percent || 0,
        reply_rate_percent: kpis.reply_rate_percent || 0,
        total_valid_emails: kpis.total_valid_emails || 0,
      })

      setEvents(outreachData || [])

      // Parse settings
      const settingsMap: Record<string, any> = {}
      for (const s of settingsList || []) {
        try {
          settingsMap[s.key] = JSON.parse(s.value_json)
        } catch {
          settingsMap[s.key] = s.value_json
        }
      }
      setSettings(settingsMap)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const runOutreach = async () => {
    try {
      setRunning(true)
      setError('')
      setSuccess('')
      await pipelinesApi.runOutreach(mode, dryRun)
      if (mode === 'mailmerge') {
        setSuccess('Mailmerge export started! Check the data/exports folder for CSV file.')
      } else {
        setSuccess(`Outreach pipeline started (dry_run=${dryRun})! Check Pipelines page for progress.`)
      }
      setTimeout(() => fetchData(), 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start outreach pipeline')
    } finally {
      setRunning(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      sent: 'bg-blue-100 text-blue-800',
      delivered: 'bg-green-100 text-green-800',
      bounced: 'bg-red-100 text-red-800',
      replied: 'bg-purple-100 text-purple-800',
      skipped: 'bg-gray-100 text-gray-800',
    }
    return colors[status?.toLowerCase()] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading outreach data...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Outreach Management</h1>
          <p className="text-gray-500 mt-1">Send emails to validated contacts</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 text-green-600 px-4 py-2 rounded-lg mb-4">
          {success}
        </div>
      )}

      {/* Workflow Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-800 mb-2">Outreach Workflow</h3>
        <div className="flex items-center text-sm text-blue-700">
          <span className="px-2 py-1 bg-blue-100 rounded">1. Leads Sourced</span>
          <span className="mx-2">→</span>
          <span className="px-2 py-1 bg-blue-100 rounded">2. Contacts Enriched</span>
          <span className="mx-2">→</span>
          <span className="px-2 py-1 bg-blue-100 rounded">3. Emails Validated</span>
          <span className="mx-2">→</span>
          <span className="px-2 py-1 bg-blue-200 rounded font-semibold">4. Outreach Sent</span>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-6 gap-4 mb-6">
        <div className="card p-4 text-center border-l-4 border-blue-500">
          <div className="text-2xl font-bold text-blue-600">{stats?.total_valid_emails || 0}</div>
          <div className="text-sm text-gray-500">Valid Emails</div>
        </div>
        <div className="card p-4 text-center border-l-4 border-green-500">
          <div className="text-2xl font-bold text-green-600">{stats?.emails_sent || 0}</div>
          <div className="text-sm text-gray-500">Emails Sent</div>
        </div>
        <div className="card p-4 text-center border-l-4 border-purple-500">
          <div className="text-2xl font-bold text-purple-600">{stats?.emails_replied || 0}</div>
          <div className="text-sm text-gray-500">Replies</div>
        </div>
        <div className="card p-4 text-center border-l-4 border-red-500">
          <div className="text-2xl font-bold text-red-600">{stats?.emails_bounced || 0}</div>
          <div className="text-sm text-gray-500">Bounced</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-gray-800">{stats?.bounce_rate_percent?.toFixed(1) || 0}%</div>
          <div className="text-sm text-gray-500">Bounce Rate</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-gray-800">{stats?.reply_rate_percent?.toFixed(1) || 0}%</div>
          <div className="text-sm text-gray-500">Reply Rate</div>
        </div>
      </div>

      {/* Outreach Controls */}
      <div className="card p-6 mb-6">
        <h3 className="font-semibold text-gray-800 mb-4">Run Outreach</h3>

        <div className="grid grid-cols-3 gap-6">
          {/* Mode Selection */}
          <div>
            <label className="label">Outreach Mode</label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as 'mailmerge' | 'send')}
              className="input"
            >
              <option value="mailmerge">Mailmerge Export (CSV)</option>
              <option value="send">Programmatic Send</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {mode === 'mailmerge'
                ? 'Export contacts to CSV for mail merge tools'
                : 'Send emails programmatically via configured provider'}
            </p>
          </div>

          {/* Dry Run Toggle */}
          {mode === 'send' && (
            <div>
              <label className="label">Dry Run</label>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={dryRun}
                  onChange={(e) => setDryRun(e.target.checked)}
                  className="w-4 h-4"
                />
                <span className="text-sm text-gray-600">
                  {dryRun ? 'Simulate only (no actual emails)' : 'Send real emails'}
                </span>
              </div>
            </div>
          )}

          {/* Run Button */}
          <div className="flex items-end">
            <button
              onClick={runOutreach}
              disabled={running}
              className="btn-primary"
            >
              {running ? 'Starting...' : mode === 'mailmerge' ? 'Export for Mailmerge' : 'Run Outreach'}
            </button>
          </div>
        </div>

        {/* Business Rules */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Business Rules Applied:</h4>
          <div className="grid grid-cols-3 gap-4 text-sm text-gray-600">
            <div>Daily Limit: <span className="font-mono">{settings.daily_send_limit || 30}</span></div>
            <div>Cooldown: <span className="font-mono">{settings.cooldown_days || 10} days</span></div>
            <div>Max per Job: <span className="font-mono">{settings.max_contacts_per_company_job || 4}</span></div>
          </div>
        </div>
      </div>

      {/* Recent Outreach Events */}
      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-800">Recent Outreach Events</h3>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Company
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sent At
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Channel
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {events.map((event, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-900">
                  {event.contact_name || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {event.client_name || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900 font-mono">
                  {event.email || '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {event.sent_at ? new Date(event.sent_at).toLocaleString() : '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {event.channel || '-'}
                </td>
                <td className="px-6 py-4">
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(event.status)}`}>
                    {event.status || '-'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {events.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No outreach events yet. Run the outreach pipeline to send emails.
          </div>
        )}
      </div>
    </div>
  )
}
