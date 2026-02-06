# Supabase Schema Reference

## Entity Relationship Diagram

```
clients (1) ──── (N) campaigns (1) ──── (N) weekly_metrics
   │                    │
   │                    └──── (N) content_log
   │
   └──── (N) client_brand_voices

winning_strategies (materialized view) ← campaigns + content_log + weekly_metrics
```

## Row Level Security (RLS) Policies

Enable RLS on all tables for production use. The Growth Engine accesses data via Supabase service role key through MCP.

```sql
-- Enable RLS
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE weekly_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE client_brand_voices ENABLE ROW LEVEL SECURITY;

-- Service role has full access (used by MCP)
CREATE POLICY "Service role full access" ON clients
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON campaigns
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON content_log
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON weekly_metrics
  FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access" ON client_brand_voices
  FOR ALL USING (auth.role() = 'service_role');
```

## Supabase Edge Functions

### Weekly Report Generator

Deploy as a Supabase Edge Function for automated weekly reports:

```typescript
// supabase/functions/weekly-report/index.ts
import { createClient } from '@supabase/supabase-js'

Deno.serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  const currentWeek = getISOWeek(new Date())
  const currentYear = new Date().getFullYear()

  // Fetch all active campaigns with last week's metrics
  const { data: metrics } = await supabase
    .from('weekly_metrics')
    .select(`
      *,
      campaigns (
        *,
        clients (name, industry)
      )
    `)
    .eq('week_number', currentWeek - 1)
    .eq('year', currentYear)

  // Calculate summary
  const summary = {
    total_spend: metrics?.reduce((sum, m) => sum + m.spend, 0),
    total_hires: metrics?.reduce((sum, m) => sum + m.hires, 0),
    avg_ctr: metrics?.reduce((sum, m) => sum + m.ctr, 0) / (metrics?.length || 1),
    campaigns_count: metrics?.length,
    top_performer: metrics?.sort((a, b) => (a.cph || Infinity) - (b.cph || Infinity))[0],
    alerts: metrics?.filter(m =>
      m.ctr < 0.005 || // CTR below 0.5%
      (m.applications === 0 && m.spend > 100) // Spend without applications
    )
  }

  return new Response(JSON.stringify(summary), {
    headers: { 'Content-Type': 'application/json' }
  })
})

function getISOWeek(date: Date): number {
  const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  const dayNum = d.getUTCDay() || 7
  d.setUTCDate(d.getUTCDate() + 4 - dayNum)
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1))
  return Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
}
```

## Data Retention Policy

| Table | Retention | Archival Strategy |
|-------|-----------|-------------------|
| weekly_metrics | Indefinite | Core training data, never delete |
| content_log | Indefinite | Essential for content performance correlation |
| campaigns | Indefinite | Reference data |
| clients | Indefinite | Reference data |
| winning_strategies | Refreshed weekly | Materialized view, auto-updated |

## Backup Strategy

- Enable Supabase Point-in-Time Recovery (PITR) on the project
- Weekly logical backups via `pg_dump` stored in Supabase Storage
- Export winning_strategies as JSON after each refresh for offline reference
