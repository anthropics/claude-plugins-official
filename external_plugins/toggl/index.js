#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

const TOGGL_API_BASE = 'https://api.track.toggl.com/api/v9';
const REPORTS_API_BASE = 'https://api.track.toggl.com/reports/api/v3';
const CREDENTIALS_FILE = join(homedir(), '.claude', 'toggl', 'credentials');

function loadToken() {
  if (process.env.TOGGL_API_TOKEN) return process.env.TOGGL_API_TOKEN.trim();
  if (existsSync(CREDENTIALS_FILE)) {
    return readFileSync(CREDENTIALS_FILE, 'utf8').trim();
  }
  process.stderr.write(
    `toggl-mcp: API token required.\n` +
    `  Option 1: set TOGGL_API_TOKEN environment variable\n` +
    `  Option 2: create ${CREDENTIALS_FILE} with your API token\n` +
    `  Get your token at: https://track.toggl.com/profile\n`
  );
  process.exit(1);
}

const API_TOKEN = loadToken();
const AUTH_HEADER = 'Basic ' + Buffer.from(`${API_TOKEN}:api_token`).toString('base64');
const COMMON_HEADERS = { 'Authorization': AUTH_HEADER, 'Content-Type': 'application/json' };

let _workspaceId = null;

async function togglFetch(baseUrl, path, method = 'GET', body = null) {
  const options = { method, headers: COMMON_HEADERS };
  if (body !== null) options.body = JSON.stringify(body);
  const res = await fetch(`${baseUrl}${path}`, options);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Toggl API ${res.status}: ${text}`);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

const api = (path, method, body) => togglFetch(TOGGL_API_BASE, path, method, body);
const reports = (path, method, body) => togglFetch(REPORTS_API_BASE, path, method, body);

async function getWorkspaceId() {
  if (_workspaceId) return _workspaceId;
  const me = await api('/me');
  _workspaceId = me.default_workspace_id;
  return _workspaceId;
}

// ─── Tool definitions ────────────────────────────────────────────────────────

const TOOLS = [
  {
    name: 'toggl_get_me',
    description:
      'Get the current Toggl user info: email, full name, timezone, and default workspace ID.',
    inputSchema: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'toggl_list_projects',
    description:
      'List projects in the Toggl workspace. Returns id, name, color, and active status. ' +
      'Use this to resolve a project name to its numeric ID before logging time.',
    inputSchema: {
      type: 'object',
      properties: {
        active_only: { type: 'boolean', description: 'Return only active projects (default: true)' },
      },
    },
  },
  {
    name: 'toggl_list_tasks',
    description:
      'List tasks inside a specific Toggl project. Returns id, name, and active status. ' +
      'Use this to resolve a task name to its numeric ID before logging time against a task.',
    inputSchema: {
      type: 'object',
      properties: {
        project_id: { type: 'number', description: 'Project ID (from toggl_list_projects)' },
      },
      required: ['project_id'],
    },
  },
  {
    name: 'toggl_list_time_entries',
    description:
      'List time entries for a date range, optionally filtered by project or task. ' +
      'Use for queries like "what did I track today / this week / on 2025-01-10".',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: { type: 'string', description: 'Start date YYYY-MM-DD (default: today)' },
        end_date:   { type: 'string', description: 'End date YYYY-MM-DD (default: same as start_date)' },
        project_id: { type: 'number', description: 'Filter entries by project ID (optional)' },
        task_id:    { type: 'number', description: 'Filter entries by task ID (optional)' },
      },
    },
  },
  {
    name: 'toggl_get_summary',
    description:
      'Get aggregated time totals grouped by project and task for a date range. ' +
      'Use for "how much time did I spend on project X this week?" or "total hours on task Y in May". ' +
      'Optionally filter to a specific project_id or task_id.',
    inputSchema: {
      type: 'object',
      properties: {
        start_date: { type: 'string', description: 'Start date YYYY-MM-DD (default: today)' },
        end_date:   { type: 'string', description: 'End date YYYY-MM-DD (default: same as start_date)' },
        project_id: { type: 'number', description: 'Limit summary to one project (optional)' },
        task_id:    { type: 'number', description: 'Limit summary to one task (optional)' },
      },
    },
  },
  {
    name: 'toggl_create_time_entry',
    description:
      'Manually log a completed time entry, optionally linked to a project and/or task. ' +
      'Resolve project name → project_id via toggl_list_projects, task name → task_id via toggl_list_tasks.',
    inputSchema: {
      type: 'object',
      properties: {
        description:      { type: 'string', description: 'What you worked on' },
        duration_minutes: { type: 'number', description: 'Duration in minutes (e.g. 90 for 1.5h)' },
        start: {
          type: 'string',
          description: 'Start time: YYYY-MM-DD (assumes 09:00 UTC) or full ISO 8601 datetime',
        },
        project_id: { type: 'number', description: 'Project ID from toggl_list_projects (optional)' },
        task_id:    { type: 'number', description: 'Task ID from toggl_list_tasks (optional)' },
        tags:       { type: 'array', items: { type: 'string' }, description: 'Tags to apply (optional)' },
        billable:   { type: 'boolean', description: 'Mark as billable (default: false)' },
      },
      required: ['description', 'duration_minutes', 'start'],
    },
  },
  {
    name: 'toggl_get_current_timer',
    description:
      'Check if a Toggl timer is currently running. Returns description, project, task, ' +
      'start time, and elapsed minutes — or {running: false} if nothing is active.',
    inputSchema: { type: 'object', properties: {}, required: [] },
  },
];

// ─── Tool handlers ───────────────────────────────────────────────────────────

async function handleGetMe() {
  const me = await api('/me');
  return {
    id: me.id,
    email: me.email,
    full_name: me.fullname,
    timezone: me.timezone,
    default_workspace_id: me.default_workspace_id,
  };
}

async function handleListProjects({ active_only = true } = {}) {
  const wid = await getWorkspaceId();
  const projects = await api(`/workspaces/${wid}/projects?active=${active_only}`);
  return (projects || []).map(p => ({
    id: p.id,
    name: p.name,
    active: p.active,
    color: p.color,
    billable: p.billable,
  }));
}

async function handleListTasks({ project_id }) {
  const wid = await getWorkspaceId();
  const tasks = await api(`/workspaces/${wid}/projects/${project_id}/tasks`);
  return (tasks || []).map(t => ({
    id: t.id,
    name: t.name,
    active: t.active,
    project_id: t.project_id,
    estimated_seconds: t.estimated_seconds ?? null,
  }));
}

async function handleListTimeEntries({ start_date, end_date, project_id, task_id } = {}) {
  const today = new Date().toISOString().slice(0, 10);
  const from = start_date || today;
  const to = end_date || from;

  const entries = await api(
    `/me/time_entries?start_date=${encodeURIComponent(`${from}T00:00:00Z`)}&end_date=${encodeURIComponent(`${to}T23:59:59Z`)}`
  );

  let results = (entries || []).map(e => ({
    id: e.id,
    description: e.description || '(no description)',
    project_id: e.project_id ?? null,
    task_id: e.task_id ?? null,
    duration_seconds: e.duration,
    duration_minutes: e.duration > 0 ? Math.round(e.duration / 60) : null,
    start: e.start,
    stop: e.stop ?? null,
    tags: e.tags || [],
    billable: e.billable,
  }));

  if (project_id) results = results.filter(e => e.project_id === project_id);
  if (task_id)    results = results.filter(e => e.task_id === task_id);

  return results;
}

async function handleGetSummary({ start_date, end_date, project_id, task_id } = {}) {
  const wid = await getWorkspaceId();
  const today = new Date().toISOString().slice(0, 10);
  const from = start_date || today;
  const to = end_date || from;

  const body = {
    start_date: from,
    end_date: to,
    grouping: 'projects',
    sub_grouping: 'tasks',
  };
  if (project_id) body.project_ids = [project_id];
  if (task_id)    body.task_ids = [task_id];

  const data = await reports(`/workspace/${wid}/summary/time_entries`, 'POST', body);

  const groups = (data?.groups || []).map(g => ({
    project_id: g.id,
    project_name: g.title?.name ?? g.title ?? null,
    total_seconds: g.seconds ?? g.tracked_seconds ?? 0,
    total_hours: formatDuration(g.seconds ?? g.tracked_seconds ?? 0),
    tasks: (g.sub_groups || []).map(s => ({
      task_id: s.id,
      task_name: s.title?.name ?? s.title ?? '(no task)',
      total_seconds: s.seconds ?? s.tracked_seconds ?? 0,
      total_hours: formatDuration(s.seconds ?? s.tracked_seconds ?? 0),
    })),
  }));

  const grandTotal = groups.reduce((sum, g) => sum + g.total_seconds, 0);

  return {
    period: { from, to },
    grand_total: formatDuration(grandTotal),
    grand_total_seconds: grandTotal,
    projects: groups,
  };
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${String(m).padStart(2, '0')}m`;
}

async function handleCreateTimeEntry({
  description,
  duration_minutes,
  start,
  project_id,
  task_id,
  tags = [],
  billable = false,
}) {
  const wid = await getWorkspaceId();

  let startISO = start;
  if (/^\d{4}-\d{2}-\d{2}$/.test(start)) {
    startISO = `${start}T09:00:00Z`;
  }

  const payload = {
    description,
    duration: Math.round(duration_minutes * 60),
    start: startISO,
    workspace_id: wid,
    created_with: 'claude-mcp-toggl',
    billable,
  };
  if (project_id) payload.project_id = project_id;
  if (task_id)    payload.task_id = task_id;
  if (tags.length) payload.tag_names = tags;

  const entry = await api(`/workspaces/${wid}/time_entries`, 'POST', payload);

  return {
    id: entry.id,
    description: entry.description,
    duration_minutes: Math.round(entry.duration / 60),
    start: entry.start,
    stop: entry.stop,
    project_id: entry.project_id ?? null,
    task_id: entry.task_id ?? null,
  };
}

async function handleGetCurrentTimer() {
  const entry = await api('/me/time_entries/current');
  if (!entry) return { running: false, entry: null };

  const elapsedMinutes = Math.round((Date.now() - new Date(entry.start).getTime()) / 60_000);

  return {
    running: true,
    entry: {
      id: entry.id,
      description: entry.description || '(no description)',
      project_id: entry.project_id ?? null,
      task_id: entry.task_id ?? null,
      start: entry.start,
      elapsed_minutes: elapsedMinutes,
      tags: entry.tags || [],
    },
  };
}

// ─── MCP server wiring ───────────────────────────────────────────────────────

const server = new Server(
  { name: 'toggl', version: '1.1.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    let result;
    switch (name) {
      case 'toggl_get_me':            result = await handleGetMe();                   break;
      case 'toggl_list_projects':     result = await handleListProjects(args);        break;
      case 'toggl_list_tasks':        result = await handleListTasks(args);           break;
      case 'toggl_list_time_entries': result = await handleListTimeEntries(args);     break;
      case 'toggl_get_summary':       result = await handleGetSummary(args);          break;
      case 'toggl_create_time_entry': result = await handleCreateTimeEntry(args);     break;
      case 'toggl_get_current_timer': result = await handleGetCurrentTimer();         break;
      default: throw new Error(`Unknown tool: ${name}`);
    }
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
  } catch (err) {
    return {
      content: [{ type: 'text', text: `Error: ${err.message}` }],
      isError: true,
    };
  }
});

process.on('unhandledRejection', err => process.stderr.write(`toggl-mcp: unhandled rejection: ${err}\n`));
process.on('uncaughtException',  err => process.stderr.write(`toggl-mcp: uncaught exception: ${err}\n`));

const transport = new StdioServerTransport();
await server.connect(transport);
