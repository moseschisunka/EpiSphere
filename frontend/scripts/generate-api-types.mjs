import { execFileSync } from 'node:child_process'
import { mkdirSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDirectory = dirname(fileURLToPath(import.meta.url))
const frontendDirectory = resolve(scriptDirectory, '..')
const source = process.env.EPISPHERE_OPENAPI_URL || 'http://127.0.0.1:8000/openapi.json'
const output = resolve(frontendDirectory, 'lib/api.generated.ts')

mkdirSync(dirname(output), { recursive: true })

const executable = resolve(frontendDirectory, 'node_modules/openapi-typescript/bin/cli.js')
execFileSync(process.execPath, [executable, source, '-o', output], {
  cwd: frontendDirectory,
  stdio: 'inherit',
})
