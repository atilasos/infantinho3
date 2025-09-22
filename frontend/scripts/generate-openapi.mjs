#!/usr/bin/env node
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFile } from 'node:child_process';

const rawSchema = process.env.API_SCHEMA_URL ?? 'http://localhost:8000/api/schema';
const schemaArg = rawSchema.startsWith('http') ? rawSchema : resolve(process.cwd(), rawSchema);

const __filename = fileURLToPath(import.meta.url);
const __dirname = resolve(__filename, '..');
const targetPath = resolve(__dirname, '../src/types/openapi.ts');

const args = [schemaArg, '--output', targetPath];

if (process.env.API_SCHEMA_TOKEN) {
  args.push('--header', `Authorization: Bearer ${process.env.API_SCHEMA_TOKEN}`);
}

console.log(`🔄  A gerar tipos a partir de ${schemaArg}`);

await new Promise((resolvePromise, rejectPromise) => {
  const child = execFile(
    resolve(__dirname, '../node_modules/.bin/openapi-typescript'),
    args,
    { stdio: 'inherit' },
    (error) => {
      if (error) {
        rejectPromise(error);
      } else {
        resolvePromise();
      }
    },
  );

  child.on('error', rejectPromise);
});

console.log(`✅  Tipos atualizados em ${targetPath}`);
