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
export type Country = ApiSchemas['CountryResponse']
export type Disease = ApiSchemas['DiseaseResponse']
export type Facility = ApiSchemas['Facility']
export type FacilityStaff = ApiResponse<operations['list_facility_staff_api_v1_facilities__facility_id__staff_get']>[number]
export type FacilityConsent = ApiResponse<operations['update_facility_consent_api_v1_facilities__facility_id__consent_put']>
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

export type CountriesResponse = ApiResponse<operations['list_countries_api_v1_countries__get']>
export type DiseasesResponse = ApiResponse<operations['list_diseases_api_v1_diseases__get']>
export type AlertStatus = ApiSchemas['AlertStatus']
export type CasesResponse = ApiResponse<operations['list_cases_api_v1_cases__get']>
export type AlertsResponse = ApiResponse<operations['list_alerts_api_v1_alerts__get']>
export type FacilitiesResponse = ApiResponse<operations['list_facilities_api_v1_facilities__get']>
export type UsersResponse = ApiResponse<operations['list_users_api_v1_users__get']>
export type RolesResponse = ApiResponse<operations['list_roles_api_v1_users_roles_get']>
export type PatientsResponse = ApiResponse<operations['list_patients_api_v1_clinical_patients_get']>
export type PrescriptionsResponse = ApiResponse<operations['list_pending_prescriptions_api_v1_pharmacy_prescriptions_get']>
export type SourceSystemsResponse = ApiResponse<operations['list_source_systems_api_v1_interop_source_systems_get']>
export type InteropLog = ApiSchemas['InteropLogResponse']
export type InteropLogsResponse = ApiResponse<operations['get_interop_logs_api_v1_interop_logs_get']>
export type PublicStatsResponse = ApiResponse<operations['get_public_stats_api_v1_public_stats_get']>
export type PublicMapPoint = ApiSchemas['PublicMapPointResponse']
export type PublicMapResponse = ApiResponse<operations['get_public_map_api_v1_public_map_get']>
export type PublicAlert = ApiSchemas['PublicAlertResponse']
export type PublicAlertsResponse = ApiResponse<operations['get_public_alerts_api_v1_public_alerts_get']>
export type PublicNewsResponse = ApiResponse<operations['get_public_news_api_v1_public_news_get']>
export type NewsResponse = ApiResponse<operations['list_news_articles_api_v1_news_get']>
export type LocationFacility = ApiSchemas['LocationFacilityResponse']
export type LocationCountry = ApiSchemas['LocationCountryResponse']
export type LocationHierarchyResponse = ApiResponse<operations['get_location_hierarchy_api_v1_locations_hierarchy_get']>
export type DistrictsResponse = ApiResponse<operations['get_districts_by_province_api_v1_locations_districts_get']>
export type ProvincesResponse = ApiResponse<operations['get_provinces_by_country_api_v1_locations_provinces_get']>
export type SyndromicTrend = ApiSchemas['SyndromicTrendResponse']
export type SyndromicTrendsResponse = ApiResponse<operations['get_syndromic_trends_api_v1_surveillance_syndromes_trends_get']>
export type FacilityHeatmapPoint = ApiSchemas['FacilityHeatmapPointResponse']
export type FacilityHeatmapResponse = ApiResponse<operations['get_facility_heatmap_api_v1_surveillance_heatmap_get']>
export type CovidIngestResponse = { message?: string; job_id?: number | null; status?: string; result?: unknown; error?: string | null }
export type IngestionResponse = ApiResponse<operations['ingest_csv_dataset_api_v1_datasets_ingest_csv_post']>
