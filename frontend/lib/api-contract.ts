import type { components, operations } from './api.generated'

export type ApiSchemas = components['schemas']

type JsonBody<Response> = Response extends { content: infer Content }
  ? Content extends { 'application/json': infer Body }
    ? Body
    : never
  : never

type SuccessResponses<Responses> = {
  [Status in keyof Responses]: Status extends 200 | 201 | 202 | 204 ? Responses[Status] : never
}[keyof Responses]

export type ApiResponse<Operation> = Operation extends { responses: infer Responses }
  ? JsonBody<SuccessResponses<Responses>>
  : never

export type ApiRequestBody<Operation, ContentType extends string = 'application/json'> =
  Operation extends { requestBody?: { content: infer Content } }
    ? Content extends Record<ContentType, infer Body>
      ? Body
      : never
    : never

export type ApiQuery<Operation> = Operation extends { parameters: { query?: infer Query } } ? Query : never
export type ApiPath<Operation> = Operation extends { parameters: { path?: infer Path } } ? Path : never

export type CurrentUser = ApiResponse<operations['get_current_user_info_api_v1_auth_me_get']>
export type Country = {
  id: number
  name: string
  iso_code: string
  iso_code_2?: string | null
  region_id?: number | null
  population?: number | null
  latitude?: number | null
  longitude?: number | null
}
export type Disease = {
  id: number
  name: string
  code: string
  description?: string | null
  biosafety_level?: string | null
  is_active: boolean
}
export type Facility = ApiSchemas['Facility']
export type Dashboard = ApiResponse<operations['get_global_dashboard_api_v1_dashboard_global_get']>
export type CountryDashboard = ApiResponse<operations['get_country_dashboard_api_v1_dashboard_country__country_id__get']>
export type Case = ApiSchemas['CaseResponse']
export type Alert = ApiSchemas['AlertResponse']
export type Patient = ApiSchemas['Patient']
export type Prescription = ApiResponse<operations['list_pending_prescriptions_api_v1_pharmacy_prescriptions_get']>[number]
export type UploadResult = ApiSchemas['CaseUploadResult']

export type RegisterRequest = ApiRequestBody<operations['register_api_v1_auth_register_post']>
export type CaseCreateRequest = ApiRequestBody<operations['create_case_api_v1_cases__post']>
export type AlertResolveRequest = ApiRequestBody<operations['resolve_alert_api_v1_alerts__alert_id__resolve_post']>
export type ForecastRequest = ApiRequestBody<operations['generate_forecast_api_v1_forecast_generate_post']>
export type FacilityCreateRequest = ApiRequestBody<operations['create_facility_api_v1_facilities__post']>
export type PatientCreateRequest = ApiRequestBody<operations['create_patient_api_v1_clinical_patients_post']>
export type EncounterCreateRequest = ApiRequestBody<operations['create_encounter_api_v1_clinical_encounters_post']>
export type DispenseRequest = ApiRequestBody<operations['dispense_medication_api_v1_pharmacy_dispense_post']>
export type Dhis2SyncRequest = ApiRequestBody<operations['trigger_dhis2_sync_api_v1_interop_dhis2_sync_post']>
export type Dhis2PullRequest = ApiRequestBody<operations['trigger_dhis2_pull_api_v1_interop_dhis2_pull_post']>
export type CsvIngestRequest = ApiRequestBody<operations['ingest_csv_dataset_api_v1_datasets_ingest_csv_post']>
export type WhoIngestRequest = ApiRequestBody<operations['ingest_who_gho_dataset_api_v1_datasets_ingest_who_post']>

export type CountriesResponse = Country[]
export type DiseasesResponse = Disease[]
export type AlertStatus = ApiSchemas['AlertStatus']
export type CasesResponse = ApiResponse<operations['list_cases_api_v1_cases__get']>
export type AlertsResponse = ApiResponse<operations['list_alerts_api_v1_alerts__get']>
export type FacilitiesResponse = ApiResponse<operations['list_facilities_api_v1_facilities__get']>
export type UsersResponse = ApiResponse<operations['list_users_api_v1_users__get']>
export type RolesResponse = ApiResponse<operations['list_roles_api_v1_users_roles_get']>
export type PatientsResponse = ApiResponse<operations['list_patients_api_v1_clinical_patients_get']>
export type PrescriptionsResponse = ApiResponse<operations['list_pending_prescriptions_api_v1_pharmacy_prescriptions_get']>
export type SourceSystemsResponse = ApiResponse<operations['list_source_systems_api_v1_interop_source_systems_get']>
export type InteropLog = {
  id: number
  system_name: string
  direction: string
  status: string
  dataset_type: string
  timestamp: string
  target_system?: string | null
}
export type InteropLogsResponse = InteropLog[]
export type PublicStatsResponse = {
  total_visits_recorded: number
  participating_facilities: number
  alert_level: string
}
export type PublicMapPoint = { type: 'facility'; name: string; lat: number; lon: number; count: number }
export type PublicMapResponse = PublicMapPoint[]
export type PublicAlert = { severity: string; message: string }
export type PublicAlertsResponse = PublicAlert[]
export type PublicNewsResponse = ApiResponse<operations['get_public_news_api_v1_public_news_get']>
export type NewsResponse = ApiResponse<operations['list_news_articles_api_v1_news_get']>
export type LocationFacility = {
  id: number
  name: string
  type: string
  province?: string | null
  district?: string | null
  latitude?: number | null
  longitude?: number | null
}
export type LocationCountry = {
  id: number
  name: string
  iso_code: string
  provinces: string[]
  districts: string[]
  facility_count: number
  facilities: LocationFacility[]
}
export type LocationHierarchyResponse = Array<{
  region_id: number
  region_name: string
  region_code: string
  countries: LocationCountry[]
}>
export type DistrictsResponse = { country_id: number; province: string; districts: string[] }
export type ProvincesResponse = { country_id: number; provinces: string[] }
export type SyndromicTrend = { date: string; [syndrome: string]: string | number }
export type SyndromicTrendsResponse = SyndromicTrend[]
export type FacilityHeatmapPoint = {
  name: string
  type: string
  facility_code?: string | null
  admin1_code?: string | null
  admin2_code?: string | null
  lat: number
  lon: number
  count: number
}
export type FacilityHeatmapResponse = FacilityHeatmapPoint[]
export type CovidIngestResponse = { message?: string; job_id?: number | null; status?: string; result?: unknown; error?: string | null }
export type IngestionResponse = ApiResponse<operations['ingest_csv_dataset_api_v1_datasets_ingest_csv_post']>
