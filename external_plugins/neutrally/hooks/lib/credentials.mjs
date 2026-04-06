/**
 * Neutrally credentials and config reader.
 * Credentials are managed by the neutrally CLI at ~/.neutrally/credentials.json
 * Plugin config lives at ~/.neutrally/plugin-config.json
 */
import { readFileSync, existsSync, writeFileSync, mkdirSync } from 'fs';
import { homedir } from 'os';
import { join, dirname } from 'path';

const NEUTRALLY_DIR = join(homedir(), '.neutrally');
const CREDENTIALS_PATH = join(NEUTRALLY_DIR, 'credentials.json');
const PLUGIN_CONFIG_PATH = join(NEUTRALLY_DIR, 'plugin-config.json');

const DEFAULT_PLUGIN_CONFIG = {
  captureIntervalMinutes: 5,
};

export function readCredentials() {
  try {
    if (!existsSync(CREDENTIALS_PATH)) return null;
    const data = JSON.parse(readFileSync(CREDENTIALS_PATH, 'utf8'));
    if (!data?.token) return null;
    return data;
  } catch {
    return null;
  }
}

export function readPluginConfig() {
  try {
    if (!existsSync(PLUGIN_CONFIG_PATH)) return { ...DEFAULT_PLUGIN_CONFIG };
    return { ...DEFAULT_PLUGIN_CONFIG, ...JSON.parse(readFileSync(PLUGIN_CONFIG_PATH, 'utf8')) };
  } catch {
    return { ...DEFAULT_PLUGIN_CONFIG };
  }
}

export function writePluginConfig(config) {
  mkdirSync(dirname(PLUGIN_CONFIG_PATH), { recursive: true });
  writeFileSync(PLUGIN_CONFIG_PATH, JSON.stringify(config, null, 2));
}

export function getApiBase(creds) {
  return (creds?.api_url || 'https://neutrally.app').replace(/\/$/, '');
}

export function getAuthHeaders(creds) {
  return {
    'Authorization': `Bearer ${creds.token}`,
    'Content-Type': 'application/json',
  };
}
