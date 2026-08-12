/**
 * API client for EpiSphere AI backend
 */

import axios from 'axios'
import type { operations } from './api.generated'
import type {
  AlertResolveRequest,
  AlertsResponse,
  AlertStatus,
  ApiPath,
  ApiQuery,
  ApiRequestBody,
  ApiResponse,
  CaseCreateRequest,
  CasesResponse,
  CountriesResponse,
  Country,
  CountryDashboard,
  CsvIngestRequest,
  Dashboard,
  DistrictsResponse,
  Dhis2PullRequest,
  Dhis2SyncRequest,
  DiseasesResponse,
  Disease,
  DispenseRequest,
  EncounterCreateRequest,
  Facility,
  FacilityCreateRequest,
  FacilitiesResponse,
  ForecastRequest,
  IngestionResponse,
  InteropLogsResponse,
  LocationHierarchyResponse,
  ProvincesResponse,
  NewsResponse,
  Patient,
  PatientCreateRequest,
  PatientsResponse,
  Prescription,
  PrescriptionsResponse,
  PublicAlertsResponse,
  PublicMapResponse,
  PublicNewsResponse,
  PublicStatsResponse,
  RegisterRequest,
  RolesResponse,
  SyndromicTrendsResponse,
  FacilityHeatmapResponse,
  CovidIngestResponse,
  SourceSystemsResponse,
  UploadResult,
  UsersResponse,
  WhoIngestRequest,
} from './api-contract'

// Point to the Next.js frontend origin, so requests go through the Next.js middleware
// which will inject the secure httpOnly cookie as a Bearer token.
const API_URL = ''

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Handle auth errors (return rejected promise so callers can handle gracefully)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(error)
  }
)

// Auth endpoints
export const authApi = {
  login: async (username: string, password: string) => {
    // Call the Next.js API route to get the httpOnly cookie securely
    const response = await axios.post('/api/auth/login', { username, password })
    return response.data
  },
  verifyMfa: async (code: string) => {
    const response = await axios.post('/api/auth/mfa/verify', { code })
    return response.data
  },
  verifyEmail: async (token: string) => {
    const response = await api.post<ApiResponse<operations['verify_email_api_v1_auth_verify_email_post']>>('/auth/verify-email', { token })
    return response.data
  },
  requestPasswordReset: async (email: string) => {
    const response = await api.post<ApiResponse<operations['request_password_reset_api_v1_auth_request_password_reset_post']>>('/auth/request-password-reset', { email })
    return response.data
  },
  resetPassword: async (token: string, password: string) => {
    const response = await api.post<ApiResponse<operations['reset_password_api_v1_auth_reset_password_post']>>('/auth/reset-password', { token, password })
    return response.data
  },
  register: async (userData: RegisterRequest) => {
    const response = await api.post<ApiResponse<operations['register_api_v1_auth_register_post']>>('/auth/register', userData)
    return response.data
  },
  getCurrentUser: async () => {
    const response = await api.get<ApiResponse<operations['get_current_user_info_api_v1_auth_me_get']>>('/auth/me')
    return response.data
  },
  logout: async () => {
    const response = await axios.post('/api/auth/logout')
    return response.data
  },
}

// Cases endpoints
export const casesApi = {
  list: async (params?: ApiQuery<operations['list_cases_api_v1_cases__get']>) => {
    const response = await api.get<CasesResponse>('/cases', { params })
    return response.data
  },
  create: async (caseData: CaseCreateRequest) => {
    const response = await api.post<ApiResponse<operations['create_case_api_v1_cases__post']>>('/cases', caseData)
    return response.data
  },
  upload: async (file: File, countryId: number, diseaseId: number, commit: boolean = true, sourceSystemCode: string = 'manual_upload') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('country_id', countryId.toString())
    formData.append('disease_id', diseaseId.toString())
    formData.append('commit', commit.toString())
    formData.append('source_system_code', sourceSystemCode)
    const response = await api.post<UploadResult>('/cases/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  getStats: async (params?: ApiQuery<operations['get_case_stats_api_v1_cases_stats_get']>) => {
    const response = await api.get<ApiResponse<operations['get_case_stats_api_v1_cases_stats_get']>>('/cases/stats', { params })
    return response.data
  },
}

// Alerts endpoints
export const alertsApi = {
  list: async (params?: ApiQuery<operations['list_alerts_api_v1_alerts__get']>) => {
    const response = await api.get<AlertsResponse>('/alerts', { params })
    return response.data
  },
  get: async (alertId: number) => {
    const response = await api.get<ApiResponse<operations['get_alert_api_v1_alerts__alert_id__get']>>(`/alerts/${alertId}`)
    return response.data
  },
  resolve: async (alertId: number, data: AlertResolveRequest) => {
    const response = await api.post<ApiResponse<operations['resolve_alert_api_v1_alerts__alert_id__resolve_post']>>(`/alerts/${alertId}/resolve`, data)
    return response.data
  },
}

// Dashboard endpoints
export const dashboardApi = {
  getGlobal: async (params?: ApiQuery<operations['get_global_dashboard_api_v1_dashboard_global_get']>) => {
    const response = await api.get<Dashboard>('/dashboard/global', { params })
    return response.data
  },
  getCountry: async (countryId: number, params?: ApiQuery<operations['get_country_dashboard_api_v1_dashboard_country__country_id__get']>) => {
    const response = await api.get<CountryDashboard>(`/dashboard/country/${countryId}`, { params })
    return response.data
  },
}

// Forecast endpoints
export const forecastApi = {
  generate: async (data: ForecastRequest) => {
    const response = await api.post<ApiResponse<operations['generate_forecast_api_v1_forecast_generate_post']>>('/forecast/generate', data)
    return response.data
  },
  list: async (params?: ApiQuery<operations['list_forecasts_api_v1_forecast__get']>) => {
    const response = await api.get<ApiResponse<operations['list_forecasts_api_v1_forecast__get']>>('/forecast', { params })
    return response.data
  },
}

// Countries and diseases
export const countriesApi = {
  list: async (): Promise<CountriesResponse> => {
    const response = await api.get<CountriesResponse>('/countries')
    return response.data
  },
  get: async (countryId: number): Promise<Country> => {
    const response = await api.get<Country>(`/countries/${countryId}`)
    return response.data
  },
}

export const diseasesApi = {
  list: async (activeOnly: boolean = true): Promise<DiseasesResponse> => {
    const response = await api.get<DiseasesResponse>('/diseases', { params: { active_only: activeOnly } })
    return response.data
  },
  get: async (diseaseId: number): Promise<Disease> => {
    const response = await api.get<Disease>(`/diseases/${diseaseId}`)
    return response.data
  },
}

export const facilitiesApi = {
  list: async (): Promise<FacilitiesResponse> => {
    const response = await api.get<FacilitiesResponse>('/facilities')
    return response.data
  },
  get: async (facilityId: number): Promise<Facility> => {
    const response = await api.get<Facility>(`/facilities/${facilityId}`)
    return response.data
  },
  staff: async (facilityId: number) => {
    const response = await api.get<ApiResponse<operations['list_facility_staff_api_v1_facilities__facility_id__staff_get']>>(`/facilities/${facilityId}/staff`)
    return response.data
  },
  updateConsent: async (facilityId: number, publicVisible: boolean) => {
    const response = await api.put<ApiResponse<operations['update_facility_consent_api_v1_facilities__facility_id__consent_put']>>(`/facilities/${facilityId}/consent`, null, { params: { public_visible: publicVisible } })
    return response.data
  },
  create: async (data: FacilityCreateRequest) => {
    const response = await api.post<ApiResponse<operations['create_facility_api_v1_facilities__post']>>('/facilities', data)
    return response.data
  }
}

export const usersApi = {
  list: async (): Promise<UsersResponse> => {
    const response = await api.get<UsersResponse>('/users')
    return response.data
  },
  roles: async (): Promise<RolesResponse> => {
    const response = await api.get<RolesResponse>('/users/roles')
    return response.data
  },
  assignRole: async (userId: number, data: { role_id: number; facility_id?: number | null; country_id?: number | null; is_verified: boolean }) => {
    const response = await api.put(`/users/${userId}/role`, data)
    return response.data
  },
}

export const clinicalApi = {
  getPatients: async (): Promise<PatientsResponse> => {
    const response = await api.get<PatientsResponse>('/clinical/patients')
    return response.data
  },
  createPatient: async (data: PatientCreateRequest) => {
    const response = await api.post<ApiResponse<operations['create_patient_api_v1_clinical_patients_post']>>('/clinical/patients', data)
    return response.data
  },
  createEncounter: async (data: EncounterCreateRequest) => {
    const response = await api.post<ApiResponse<operations['create_encounter_api_v1_clinical_encounters_post']>>('/clinical/encounters', data)
    return response.data
  }
}

export const pharmacyApi = {
  getPending: async (): Promise<PrescriptionsResponse> => {
    const response = await api.get<PrescriptionsResponse>('/pharmacy/prescriptions')
    return response.data
  },
  dispense: async (data: DispenseRequest) => {
    const response = await api.post<ApiResponse<operations['dispense_medication_api_v1_pharmacy_dispense_post']>>('/pharmacy/dispense', data)
    return response.data
  }
}

export const surveillanceApi = {
  getSyndromicTrends: async (days: number = 7) => {
    const response = await api.get<SyndromicTrendsResponse>('/surveillance/syndromes/trends', { params: { days } })
    return response.data
  },
  getHeatmap: async () => {
    const response = await api.get<FacilityHeatmapResponse>('/surveillance/heatmap')
    return response.data
  }
}

export const interopApi = {
  getSourceSystems: async (): Promise<SourceSystemsResponse> => {
    const response = await api.get<SourceSystemsResponse>('/interop/source-systems')
    return response.data
  },
  getLogs: async (): Promise<InteropLogsResponse> => {
    const response = await api.get<InteropLogsResponse>('/interop/logs')
    return response.data
  },
  syncDHIS2: async (dataset: string, payload: Dhis2SyncRequest['payload'], dryRun: boolean = false, mappingId?: number) => {
    const request: Dhis2SyncRequest = { dataset, payload, dry_run: dryRun, mapping_id: mappingId, enqueue: !dryRun }
    const response = await api.post<ApiResponse<operations['trigger_dhis2_sync_api_v1_interop_dhis2_sync_post']>>('/interop/dhis2/sync', request)
    return response.data
  },
  pullDHIS2: async (dataset_id: string, org_unit: string, period: string, mapping: Dhis2PullRequest['mapping'], country_id: number, dry_run: boolean = false) => {
    const request: Dhis2PullRequest = { dataset_id, org_unit, period, mapping, country_id, dry_run, enqueue: !dry_run }
    const response = await api.post<ApiResponse<operations['trigger_dhis2_pull_api_v1_interop_dhis2_pull_post']>>('/interop/dhis2/pull', request)
    return response.data
  }
}

export const publicApi = {
  getStats: async () => {
    const response = await api.get<PublicStatsResponse>('/public/stats')
    return response.data
  },
  getMap: async () => {
    const response = await api.get<PublicMapResponse>('/public/map')
    return response.data
  },
  getAlerts: async () => {
    const response = await api.get<PublicAlertsResponse>('/public/alerts')
    return response.data
  },
  getNews: async () => {
    const response = await api.get<PublicNewsResponse>('/public/news')
    return response.data
  }
}

export const newsApi = {
  list: async (params?: ApiQuery<operations['list_news_articles_api_v1_news_get']>) => {
    const response = await api.get<NewsResponse>('/news', { params })
    return response.data
  },
  get: async (id: number) => {
    const response = await api.get<ApiResponse<operations['get_news_article_api_v1_news__article_id__get']>>(`/news/${id}`)
    return response.data
  },
  create: async (data: ApiRequestBody<operations['create_news_article_api_v1_news_post']>) => {
    const response = await api.post<ApiResponse<operations['create_news_article_api_v1_news_post']>>('/news', data)
    return response.data
  },
  update: async (id: number, data: ApiRequestBody<operations['update_news_article_api_v1_news__article_id__put']>) => {
    const response = await api.put<ApiResponse<operations['update_news_article_api_v1_news__article_id__put']>>(`/news/${id}`, data)
    return response.data
  },
  delete: async (id: number) => {
    const response = await api.delete<ApiResponse<operations['delete_news_article_api_v1_news__article_id__delete']>>(`/news/${id}`)
    return response.data
  }
}

export const covidIngestApi = {
  seedCountries: async () => {
    const response = await api.post<CovidIngestResponse>('/covid19/seed-countries')
    return response.data
  },
  triggerIngest: async (isoCodes?: string[]) => {
    const response = await api.post<CovidIngestResponse>('/covid19/ingest', null, { params: { iso_codes: isoCodes?.join(',') } })
    return response.data
  },
  getStatus: async () => {
    const response = await api.get<CovidIngestResponse>('/covid19/status')
    return response.data
  }
}

export const locationsApi = {
  getHierarchy: async (params?: ApiQuery<operations['get_location_hierarchy_api_v1_locations_hierarchy_get']>) => {
    const response = await api.get<LocationHierarchyResponse>('/locations/hierarchy', { params })
    return response.data
  },
  getProvinces: async (countryId: number) => {
    const response = await api.get<ProvincesResponse>('/locations/provinces', { params: { country_id: countryId } })
    return response.data
  },
  getDistricts: async (countryId: number, province: string) => {
    const response = await api.get<DistrictsResponse>('/locations/districts', { params: { country_id: countryId, province } })
    return response.data
  }
}

export const datasetsApi = {
  ingestCsv: async (url: string, mapping: CsvIngestRequest['mapping'], diseaseId: number, dryRun: boolean = false) => {
    const request: CsvIngestRequest = { url, mapping, disease_id: diseaseId, dry_run: dryRun, enqueue: !dryRun }
    const response = await api.post<IngestionResponse>('/datasets/ingest-csv', request)
    return response.data
  },
  ingestWho: async (indicatorCode: string, diseaseId: number, dryRun: boolean = false) => {
    const request: WhoIngestRequest = { indicator_code: indicatorCode, disease_id: diseaseId, dry_run: dryRun, enqueue: !dryRun }
    const response = await api.post<ApiResponse<operations['ingest_who_gho_dataset_api_v1_datasets_ingest_who_post']>>('/datasets/ingest-who', request)
    return response.data
  }
}

export default api

