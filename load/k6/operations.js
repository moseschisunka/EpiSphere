import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = (__ENV.BASE_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const accessToken = __ENV.ACCESS_TOKEN;
const runIngestion = __ENV.RUN_INGESTION_DRY_RUN === 'true';
const datasetAgentKey = __ENV.DATASET_AGENT_API_KEY;
const datasetUrl = __ENV.DATASET_URL;
const datasetDiseaseId = Number(__ENV.DATASET_DISEASE_ID || 0);

if (!accessToken) {
  throw new Error('ACCESS_TOKEN for an epidemiologist or administrator is required.');
}
if (runIngestion && (!datasetAgentKey || !datasetUrl || !datasetDiseaseId)) {
  throw new Error('Dry-run ingestion requires DATASET_AGENT_API_KEY, DATASET_URL, and DATASET_DISEASE_ID.');
}

const userHeaders = {
  Authorization: `Bearer ${accessToken}`,
  'X-Request-ID': `k6-${__VU}-${__ITER}`,
};

export const options = {
  scenarios: {
    surveillance_reads: {
      executor: 'constant-vus',
      vus: Number(__ENV.READ_VUS || 5),
      duration: __ENV.READ_DURATION || '2m',
      exec: 'readOperations',
    },
    ingestion_dry_run: {
      executor: 'per-vu-iterations',
      vus: runIngestion ? 1 : 0,
      iterations: runIngestion ? Number(__ENV.INGESTION_ITERATIONS || 3) : 0,
      maxDuration: '10m',
      exec: 'ingestionDryRun',
      startTime: '5s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<800', 'p(99)<1500'],
  },
};

function get(path, name) {
  const response = http.get(`${baseUrl}${path}`, { headers: userHeaders, tags: { name } });
  check(response, { [`${name} returns 200`]: (r) => r.status === 200 });
  return response;
}

export function readOperations() {
  get('/health', 'health');
  get('/ready/components', 'readiness');
  get('/api/v1/dashboard/global', 'global_dashboard');
  get('/api/v1/dashboard/operations', 'operations_dashboard');
  get('/api/v1/alerts/?limit=50', 'alerts');
  get('/api/v1/forecast/?limit=50', 'forecasts');
  sleep(1);
}

export function ingestionDryRun() {
  const payload = JSON.stringify({
    url: datasetUrl,
    disease_id: datasetDiseaseId,
    mapping: {
      country_iso: __ENV.DATASET_COUNTRY_COLUMN || 'Country',
      date: __ENV.DATASET_DATE_COLUMN || 'Date',
      daily_cases: __ENV.DATASET_CASES_COLUMN || 'Cases',
    },
    mapping_version: 'k6-dry-run-v1',
    dry_run: true,
    enqueue: true,
  });
  const response = http.post(`${baseUrl}/api/v1/datasets/ingest-csv`, payload, {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': datasetAgentKey,
      'X-Request-ID': `k6-ingestion-${__VU}-${__ITER}`,
    },
    tags: { name: 'ingestion_dry_run' },
  });
  check(response, {
    'ingestion dry run is accepted': (r) => r.status === 200 || r.status === 202,
    'ingestion dry run returns a job': (r) => r.json('job_id') !== undefined,
  });
}
