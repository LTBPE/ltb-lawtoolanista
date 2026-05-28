import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api'

const FUNCTION_KEY = import.meta.env.VITE_FUNCTION_KEY || ''

export const api = axios.create({
  baseURL: BASE_URL,
  params: FUNCTION_KEY ? { code: FUNCTION_KEY } : {},
  headers: { 'Content-Type': 'application/json' },
})

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ScanHistory {
  id: number
  court_id: number
  scanned_at: string
  content_hash: string | null
  status: string
  error_message: string | null
  response_time_ms: number | null
}

export interface Court {
  id: number
  name: string
  url: string
  court_type: string
  state: string | null
  category: string
  active: boolean
  js_required: boolean
  css_selector: string | null
  last_scanned_at: string | null
  last_content_hash: string | null
  last_changed_at: string | null
  consecutive_errors: number
  notes: string | null
  created_at: string
  updated_at: string | null
  recent_scans: ScanHistory[]
}

export interface CourtCreate {
  name: string
  url: string
  court_type?: string
  state?: string | null
  category?: string
  active?: boolean
  js_required?: boolean
  css_selector?: string | null
  notes?: string | null
}

export interface CourtListResponse {
  items: Court[]
  total: number
  page: number
  page_size: number
}

export interface Change {
  id: number
  court_id: number
  detected_at: string
  old_snapshot_path: string
  new_snapshot_path: string
  diff_text: string | null
  diff_line_count: number
  ai_is_relevant: boolean | null
  ai_summary: string | null
  ai_category: string | null
  ai_priority: string | null
  ai_action: string | null
  sharepoint_item_id: string | null
  email_sent: boolean
  status: string
  reviewed_by: string | null
  reviewed_at: string | null
  resolution_notes: string | null
  court_name: string | null
  court_url: string | null
}

export interface ChangeListResponse {
  items: Change[]
  total: number
  page: number
  page_size: number
}

export interface DashboardStats {
  total_courts: number
  active_courts: number
  scanned_today: number
  scanned_this_week: number
  changes_new: number
  changes_this_week: number
  error_count: number
  last_scan_at: string | null
}

export interface AlertConfig {
  id: number
  email_recipients: string
  notify_immediately: boolean
  notify_digest_time: string | null
  min_priority: string
  ai_filter_enabled: boolean
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

export async function getDashboard(): Promise<DashboardStats> {
  const res = await api.get<DashboardStats>('/dashboard')
  return res.data
}

export async function getCourts(params?: {
  page?: number
  page_size?: number
  state?: string
  active?: boolean
  court_type?: string
}): Promise<CourtListResponse> {
  const res = await api.get<CourtListResponse>('/courts', { params })
  return res.data
}

export async function getCourt(id: number): Promise<Court> {
  const res = await api.get<Court>(`/courts/${id}`)
  return res.data
}

export async function createCourt(data: CourtCreate): Promise<Court> {
  const res = await api.post<Court>('/courts', data)
  return res.data
}

export async function updateCourt(
  id: number,
  data: Partial<CourtCreate>
): Promise<Court> {
  const res = await api.put<Court>(`/courts/${id}`, data)
  return res.data
}

export async function deleteCourt(id: number): Promise<void> {
  await api.delete(`/courts/${id}`)
}

export async function triggerScan(id: number): Promise<{ message: string }> {
  const res = await api.post<{ message: string }>(`/courts/${id}/scan`)
  return res.data
}

export async function getChanges(params?: {
  page?: number
  page_size?: number
  status?: string
  priority?: string
  date_from?: string
  date_to?: string
}): Promise<ChangeListResponse> {
  const res = await api.get<ChangeListResponse>('/changes', { params })
  return res.data
}

export async function getChange(id: number): Promise<Change> {
  const res = await api.get<Change>(`/changes/${id}`)
  return res.data
}

export async function updateChangeStatus(
  id: number,
  data: { status: string; reviewed_by?: string; resolution_notes?: string }
): Promise<Change> {
  const res = await api.put<Change>(`/changes/${id}/status`, data)
  return res.data
}

export async function getAlertConfig(): Promise<AlertConfig> {
  const res = await api.get<AlertConfig>('/config')
  return res.data
}

export async function updateAlertConfig(
  data: Partial<AlertConfig>
): Promise<AlertConfig> {
  const res = await api.put<AlertConfig>('/config', data)
  return res.data
}
