'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { apiGet, apiPost } from '../lib/api'

type Business = {
  id: number
  name: string
  website?: string
  phone?: string
  email?: string
  latitude?: number
  longitude?: number
  facebook?: string
  instagram?: string
  linkedin?: string
}

type BusinessRow = Business & {
  seoScore: number | string
  leadScore: number | string
}

type OutreachState = {
  subject: string
  email: string
  loading: boolean
  error?: string
  open: boolean
}

const scoreRanges = {
  all: () => true,
  '80-100': (score: number | string) => {
    const value = Number(score)
    return !Number.isNaN(value) && value >= 80 && value <= 100
  },
  '50-79': (score: number | string) => {
    const value = Number(score)
    return !Number.isNaN(value) && value >= 50 && value <= 79
  },
  'below-50': (score: number | string) => {
    const value = Number(score)
    return !Number.isNaN(value) && value < 50
  },
}

const badgeClass = (score: number | string) => {
  const value = Number(score)
  if (Number.isNaN(value)) return 'bg-gray-100 text-gray-800'
  if (value >= 80) return 'bg-emerald-100 text-emerald-800'
  if (value >= 50) return 'bg-amber-100 text-amber-800'
  return 'bg-rose-100 text-rose-800'
}

export default function Page() {
  const [businesses, setBusinesses] = useState<BusinessRow[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [leadFilter, setLeadFilter] = useState<'all' | '80-100' | '50-79' | 'below-50'>('all')
  const [seoFilter, setSeoFilter] = useState<'all' | '80-100' | '50-79' | 'below-50'>('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [outreachState, setOutreachState] = useState<Record<number, OutreachState>>({})

  useEffect(() => {
    async function loadBusinesses() {
      setLoading(true)
      setError('')

      try {
        const data = await apiGet<Business[]>('/businesses')

        const rows = await Promise.all(
          data.map(async business => {
            try {
              const scoreData = await apiPost<{ seo_score?: number; lead_score?: number }>(`/lead-score/${business.id}`)
              return {
                ...business,
                seoScore: scoreData.seo_score ?? 'N/A',
                leadScore: scoreData.lead_score ?? 'N/A',
              }
            } catch {
              return { ...business, seoScore: 'N/A', leadScore: 'N/A' }
            }
          })
        )

        setBusinesses(rows)
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Unable to load businesses.')
      } finally {
        setLoading(false)
      }
    }

    loadBusinesses()
  }, [])

  const filteredBusinesses = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase()

    return businesses.filter(business => {
      const matchesSearch =
        !normalizedSearch ||
        business.name.toLowerCase().includes(normalizedSearch) ||
        (business.website?.toLowerCase().includes(normalizedSearch) ?? false)

      const matchesLead = scoreRanges[leadFilter](business.leadScore)
      const matchesSeo = scoreRanges[seoFilter](business.seoScore)

      return matchesSearch && matchesLead && matchesSeo
    })
  }, [businesses, searchTerm, leadFilter, seoFilter])

  const statistics = useMemo(() => {
    const total = businesses.length
    const withWebsite = businesses.filter(b => b.website).length
    const withEmail = businesses.filter(b => b.email).length
    const validLeadScores = businesses
      .map(b => Number(b.leadScore))
      .filter(value => !Number.isNaN(value))

    const averageLeadScore =
      validLeadScores.length > 0
        ? Math.round(validLeadScores.reduce((sum, value) => sum + value, 0) / validLeadScores.length)
        : 'N/A'

    return { total, withWebsite, withEmail, averageLeadScore }
  }, [businesses])

  const toggleOutreach = (businessId: number) => {
    setOutreachState(prev => ({
      ...prev,
      [businessId]: {
        subject: prev[businessId]?.subject ?? '',
        email: prev[businessId]?.email ?? '',
        loading: false,
        error: prev[businessId]?.error,
        open: !prev[businessId]?.open,
      },
    }))
  }

  const generateOutreach = async (businessId: number) => {
    setOutreachState(prev => ({
      ...prev,
      [businessId]: {
        subject: prev[businessId]?.subject ?? '',
        email: prev[businessId]?.email ?? '',
        loading: true,
        error: '',
        open: true,
      },
    }))

    try {
      const data = await apiPost<{ subject?: string; email?: string; email_body?: string }>(`/outreach/${businessId}`)
      setOutreachState(prev => ({
        ...prev,
        [businessId]: {
          subject: data.subject ?? '',
          email: data.email ?? data.email_body ?? '',
          loading: false,
          error: '',
          open: true,
        },
      }))
    } catch (err: unknown) {
      setOutreachState(prev => ({
        ...prev,
        [businessId]: {
          subject: prev[businessId]?.subject ?? '',
          email: prev[businessId]?.email ?? '',
          loading: false,
          error: err instanceof Error ? err.message : 'Unable to generate outreach.',
          open: true,
        },
      }))
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-3xl bg-white p-8 shadow-sm">
            <div className="h-6 w-48 animate-pulse rounded bg-slate-200" />
            <div className="mt-6 space-y-4">
              <div className="h-24 rounded-3xl bg-slate-200" />
              <div className="h-96 rounded-3xl bg-slate-200" />
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Dashboard</h1>
            <p className="mt-1 text-sm text-slate-500">Overview of businesses, scores, and outreach.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 md:grid-cols-4">
            <div className="rounded-3xl bg-white p-5 shadow-sm">
              <p className="text-sm font-medium text-slate-500">Total Businesses</p>
              <p className="mt-3 text-3xl font-semibold text-slate-900">{statistics.total}</p>
            </div>
            <div className="rounded-3xl bg-white p-5 shadow-sm">
              <p className="text-sm font-medium text-slate-500">With Website</p>
              <p className="mt-3 text-3xl font-semibold text-slate-900">{statistics.withWebsite}</p>
            </div>
            <div className="rounded-3xl bg-white p-5 shadow-sm">
              <p className="text-sm font-medium text-slate-500">With Email</p>
              <p className="mt-3 text-3xl font-semibold text-slate-900">{statistics.withEmail}</p>
            </div>
            <div className="rounded-3xl bg-white p-5 shadow-sm">
              <p className="text-sm font-medium text-slate-500">Average Lead Score</p>
              <p className="mt-3 text-3xl font-semibold text-slate-900">{statistics.averageLeadScore}</p>
            </div>
          </div>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <div className="grid gap-4 lg:grid-cols-[1fr_auto]">
            <div className="space-y-2">
              <label htmlFor="search" className="text-sm font-medium text-slate-700">
                Search
              </label>
              <input
                id="search"
                value={searchTerm}
                onChange={event => setSearchTerm(event.target.value)}
                placeholder="Search by name or website"
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-slate-900 outline-none focus:border-slate-400"
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="lead-filter" className="text-sm font-medium text-slate-700">
                  Lead Score
                </label>
                <select
                  id="lead-filter"
                  value={leadFilter}
                  onChange={event => setLeadFilter(event.target.value as typeof leadFilter)}
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none"
                >
                  <option value="all">All</option>
                  <option value="80-100">80–100</option>
                  <option value="50-79">50–79</option>
                  <option value="below-50">Below 50</option>
                </select>
              </div>
              <div>
                <label htmlFor="seo-filter" className="text-sm font-medium text-slate-700">
                  SEO Score
                </label>
                <select
                  id="seo-filter"
                  value={seoFilter}
                  onChange={event => setSeoFilter(event.target.value as typeof seoFilter)}
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none"
                >
                  <option value="all">All</option>
                  <option value="80-100">80–100</option>
                  <option value="50-79">50–79</option>
                  <option value="below-50">Below 50</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {error ? (
          <div className="rounded-3xl bg-white p-6 text-sm text-rose-700 shadow-sm">
            {error}
          </div>
        ) : null}

        <div className="rounded-3xl bg-white p-6 shadow-sm overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead>
              <tr className="text-left text-sm font-semibold text-slate-700">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Website</th>
                <th className="px-4 py-3">Phone</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">SEO Score</th>
                <th className="px-4 py-3">Lead Score</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-sm text-slate-700">
              {filteredBusinesses.map(business => {
                const outreach = outreachState[business.id]
                return (
                  <tr key={business.id}>
                    <td className="whitespace-nowrap px-4 py-4 font-medium">{business.name}</td>
                    <td className="px-4 py-4">
                      {business.website ? (
                        <a href={business.website} target="_blank" rel="noreferrer" className="text-sky-600 hover:underline">
                          {business.website}
                        </a>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td className="px-4 py-4">{business.phone ?? 'N/A'}</td>
                    <td className="px-4 py-4">{business.email ?? 'N/A'}</td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${badgeClass(business.seoScore)}`}>
                        {business.seoScore}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${badgeClass(business.leadScore)}`}>
                        {business.leadScore}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex flex-wrap gap-2">
                        <Link href={`/business/${business.id}`} className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition hover:bg-slate-700">
                          View
                        </Link>
                        <button
                          type="button"
                          onClick={() => generateOutreach(business.id)}
                          className="rounded-full bg-sky-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-sky-500"
                        >
                          Generate Outreach
                        </button>
                        <button
                          type="button"
                          onClick={() => toggleOutreach(business.id)}
                          className="rounded-full bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-200"
                        >
                          {outreach?.open ? 'Hide' : 'Preview'}
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

          {filteredBusinesses.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-slate-500">No businesses match the current search or filters.</div>
          ) : null}

          {filteredBusinesses.map(business => {
            const outreach = outreachState[business.id]
            if (!outreach?.open) return null

            return (
              <div key={`outreach-${business.id}`} className="mt-4 rounded-3xl border border-slate-200 bg-slate-50 p-5 shadow-sm">
                {outreach.loading ? (
                  <p className="text-sm text-slate-600">Generating outreach...</p>
                ) : outreach.error ? (
                  <p className="text-sm text-rose-700">{outreach.error}</p>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <p className="text-sm font-medium text-slate-500">Subject</p>
                      <p className="mt-2 text-slate-900">{outreach.subject || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-500">Email Body</p>
                      <textarea
                        readOnly
                        value={outreach.email || ''}
                        className="mt-2 h-40 w-full rounded-3xl border border-slate-200 bg-white p-4 text-sm text-slate-900 outline-none resize-none"
                      />
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </main>
  )
}
