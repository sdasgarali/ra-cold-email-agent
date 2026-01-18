'use client'

import { useState, useEffect } from 'react'
import { settingsApi } from '@/lib/api'

interface Setting {
  key: string
  value_json: string
  type: string
  description: string
  updated_by: string
  updated_at: string
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      setLoading(true)
      const response = await settingsApi.list()
      setSettings(response || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch settings')
    } finally {
      setLoading(false)
    }
  }

  const parseValue = (valueJson: string) => {
    try {
      const parsed = JSON.parse(valueJson)
      if (typeof parsed === 'boolean') return parsed ? 'Yes' : 'No'
      return String(parsed)
    } catch {
      return valueJson
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading settings...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Settings</h1>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 px-4 py-2 rounded-lg mb-4">
          {error}
        </div>
      )}

      <div className="card">
        <div className="divide-y divide-gray-200">
          {settings.map((setting) => (
            <div key={setting.key} className="py-4 px-6 flex justify-between items-center">
              <div>
                <div className="text-sm font-medium text-gray-900">{setting.key}</div>
                <div className="text-sm text-gray-500">{setting.description}</div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm font-mono bg-gray-100 px-3 py-1 rounded">
                  {parseValue(setting.value_json)}
                </span>
                <span className="text-xs text-gray-400">{setting.type}</span>
              </div>
            </div>
          ))}
        </div>

        {settings.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No settings found
          </div>
        )}
      </div>
    </div>
  )
}
