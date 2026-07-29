'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { apiGet, apiPost } from '../../../lib/api'

type Business = {
  id: number
  name: string
  website?: string
  phone?: string
  latitude?: number
  longitude?: number
  email?: string
  facebook?: string
  instagram?: string
  linkedin?: string
}

type OutreachResult = {
  subject: string
  email: string
}

type EmailResponse = {
  status: string
  to?: string
  subject?: string
  error?: string
}

function parseScore(value: number | string | undefined) {
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function scoreBadge(score: number | string | undefined) {
  const parsed = parseScore(score)
  if (parsed === null) {
    return 'bg-gray-100 text-gray-800'
  }

  if (parsed >= 80) return 'bg-emerald-100 text-emerald-800'
  if (parsed >= 50) return 'bg-amber-100 text-amber-800'
  return 'bg-rose-100 text-rose-800'
}

export default function Page({ params }: { params: { id: string } }) {
  const [business, setBusiness] = useState<Business | null>(null)
  const [seoScore, setSeoScore] = useState<number | string>('N/A')
  const [leadScore, setLeadScore] = useState<number | string>('N/A')
  const [outreach, setOutreach] = useState<OutreachResult | null>(null)
  const [emailResponse, setEmailResponse] = useState<EmailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [outreachLoading, setOutreachLoading] = useState(false)
  const [emailLoading, setEmailLoading] = useState(false)

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError(false)
      setEmailResponse(null)

      try {
        const businessData = await apiGet<Business>(`/businesses/${params.id}`)
        setBusiness(businessData)

        const leadData = await apiPost<{ seo_score?: number; lead_score?: number }>(`/lead-score/${params.id}`)
        const outreachData = await apiPost<{ subject?: string; email?: string; email_body?: string }>(`/outreach/${params.id}`)

        setSeoScore(leadData.seo_score ?? 'N/A')
        setLeadScore(leadData.lead_score ?? 'N/A')
        setOutreach({
          subject: outreachData.subject ?? '',
          email: outreachData.email ?? outreachData.email_body ?? '',
        })
      } catch (err) {
        setError(true)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [params.id])

  const refreshOutreach = async () => {
    if (!business) return
    setOutreachLoading(true)
    setEmailResponse(null)

    try {
      const data = await apiPost<{ subject?: string; email?: string; email_body?: string }>(`/outreach/${params.id}`)
      setOutreach({
        subject: data.subject ?? '',
        email: data.email ?? data.email_body ?? '',
      })
    } catch (err) {
      setError(true)
    } finally {
      setOutreachLoading(false)
    }
  }

  const sendEmail = async () => {
    if (!business) return
    setEmailLoading(true)
    setEmailResponse(null)

    try {
      const data = await apiPost<{ status?: string; to?: string; subject?: string; error?: string }>(`/send-email/${params.id}`, {
        to: 'test@example.com',
      })

      setEmailResponse({
        status: data.status ?? 'sent',
        to: data.to,
        subject: data.subject,
        error: data.error,
      })
    } catch (err: unknown) {
      setEmailResponse({ status: 'error', error: err instanceof Error ? err.message : 'Unable to send email.' })
    } finally {
      setEmailLoading(false)
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="rounded-xl bg-white shadow-sm p-8">
            <p className="text-lg font-medium">Loading...</p>
          </div>
        </div>
      </main>
    )
  }

  if (error || !business) {
    return (
      <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="rounded-xl bg-white shadow-sm p-8">
            <p className="text-lg font-medium text-red-600">Unable to load business.</p>
            <div className="mt-4">
              <Link href="/" className="text-sky-600 hover:underline">
                Back to businesses
              </Link>
            </div>
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-bold">Business Details</h1>
            <p className="text-sm text-gray-600">Review details, scores, outreach, and email actions.</p>
          </div>
          <Link href="/" className="inline-flex rounded-md bg-slate-100 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200">
            Back to businesses
          </Link>
        </div>

        <div className="rounded-3xl bg-white p-6 shadow-sm">
          <div className="mb-6 space-y-4">
            <div className="text-xl font-semibold">{business.name}</div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <div className="text-sm font-medium text-slate-500">Website</div>
                {business.website ? (
                  <a href={business.website} target="_blank" rel="noreferrer" className="text-sky-600 hover:underline">
                    {business.website}
                  </a>
                ) : (
                  <div className="text-slate-700">N/A</div>
                )}
              </div>
              <div>
                <div className="text-sm font-medium text-slate-500">Phone</div>
                <div className="text-slate-700">{business.phone ?? 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-slate-500">Email</div>
                <div className="text-slate-700">{business.email ?? 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-slate-500">Facebook</div>
                <div className="text-slate-700">{business.facebook ?? 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-slate-500">Instagram</div>
                <div className="text-slate-700">{business.instagram ?? 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-slate-500">LinkedIn</div>
                <div className="text-slate-700">{business.linkedin ?? 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-slate-500">Latitude</div>
                <div className="text-slate-700">{business.latitude ?? 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm font-medium text-slate-500">Longitude</div>
                <div className="text-slate-700">{business.longitude ?? 'N/A'}</div>
              </div>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-sm font-medium text-slate-500">SEO Score</div>
              <div className={`mt-2 inline-flex rounded-full px-3 py-1 text-sm font-semibold ${scoreBadge(seoScore)}`}>
                {seoScore}
              </div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <div className="text-sm font-medium text-slate-500">Lead Score</div>
              <div className={`mt-2 inline-flex rounded-full px-3 py-1 text-sm font-semibold ${scoreBadge(leadScore)}`}>
                {leadScore}
              </div>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            <div>
              <div className="text-sm font-medium text-slate-500">Outreach Subject</div>
              <div className="mt-2 rounded-2xl bg-slate-50 p-4 text-slate-900">{outreach?.subject ?? 'N/A'}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-slate-500">Email Body</div>
              <textarea
                readOnly
                value={outreach?.email ?? ''}
                className="mt-2 h-48 w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-900 outline-none resize-none"
              />
            </div>
          </div>

          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={refreshOutreach}
              disabled={outreachLoading}
              className="inline-flex items-center justify-center rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {outreachLoading ? 'Refreshing...' : 'Generate Outreach'}
            </button>
            <div className="space-y-3 sm:space-y-0 sm:flex sm:items-center sm:gap-3">
              <button
                type="button"
                onClick={sendEmail}
                disabled={emailLoading}
                className="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {emailLoading ? 'Sending...' : 'Send Email'}
              </button>
              <Link
                href="/"
                className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Back to businesses
              </Link>
            </div>
          </div>

          {emailResponse ? (
            <div className="mt-4 rounded-2xl bg-slate-50 p-4 text-sm text-slate-800">
              {emailResponse.status === 'sent' ? (
                <div>
                  <div className="font-semibold text-slate-900">Email sent</div>
                  <div>To: {emailResponse.to}</div>
                  <div>Subject: {emailResponse.subject}</div>
                </div>
              ) : (
                <div className="text-rose-700">{emailResponse.error ?? 'Unable to send email.'}</div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </main>
  )
}
