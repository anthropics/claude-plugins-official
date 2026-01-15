---
name: brand-influencers
version: 2025-01-13
description: Discover influencers and partnership opportunities for a brand using XPOZ MCP. Classifies influencers by tier (Mega/Macro/Micro/Nano), voice type, sentiment, and partnership potential. Use when asked to "find influencers", "partnership opportunities", "who's talking about X", or "top voices for X".
---

# Brand Influencers Skill

## Overview

This skill provides comprehensive influencer discovery and partnership opportunity analysis. It fetches users discussing a brand, classifies them by reach tier, voice type, and sentiment, then identifies the best partnership candidates and rising stars.

## When to Use

Activate this skill when the user asks about:
- "Find influencers for [BRAND]"
- "Partnership opportunities for [BRAND]"
- "Who's talking about [BRAND]?"
- "Top voices on [BRAND/TOPIC]"
- "Influencer discovery for [BRAND]"
- "Brand ambassadors for [BRAND]"

## XPOZ MCP Data Flow

### Step 1: Query Expansion (CRITICAL!)

Expand the brand name to capture all mentions:

```
NVIDIA → "NVIDIA" OR "$NVDA"
Tesla → "Tesla" OR "$TSLA"
```

### Step 2: Fetch Users (200+ required)

```
Use getTwitterUsersByKeywords with:
- query: Expanded brand query
- fields: ["id", "username", "name", "description", "followersCount", "relevantTweetsCount", "relevantTweetsLikesSum", "relevantTweetsRetweetsSum"]
- userPrompt: "Finding influencers discussing [BRAND]"
```

**CRITICAL: Async Polling Pattern**
1. The API returns an `operationId`
2. Call `checkOperationStatus` with that operationId
3. Poll until status is "completed" (up to 8 times, ~5 seconds between)

### Step 3: Fetch Sample Tweets

```
Use getTwitterPostsByKeywords with:
- query: Same expanded query
- fields: ["id", "text", "authorUsername", "createdAtDate", "likeCount", "retweetCount"]
- userPrompt: "Fetching sample tweets for influencer quotes"
```

### Step 4: Classification Logic

**Tier Classification (by follower count):**

| Tier | Followers | Icon |
|------|-----------|------|
| Mega | 1M+ | Crown |
| Macro | 100K-1M | Star |
| Micro | 10K-100K | Sparkle |
| Nano | <10K | Dot |

**Voice Type Classification:**

| Voice Type | Indicators |
|------------|------------|
| analyst | "analysis", "research", financial terms |
| trader | "trade", "position", "calls", options language |
| news | media outlet, journalist, news in bio |
| official | brand account, verified brand |
| researcher | PhD, professor, research institution |
| influencer | creator, content, social media focus |
| founder | CEO, founder, co-founder, startup founder |
| interviewer | podcast host, show host, media interviewer |
| community | fan accounts, community managers, enthusiast groups |

**Sentiment Classification:**
- **positive**: Bullish, supportive, enthusiastic language
- **leaning_positive**: Generally favorable but measured
- **neutral**: Factual, balanced, no clear stance
- **leaning_negative**: Concerns expressed but not hostile
- **negative**: Bearish, critical, hostile language

**Partnership Score (0-100):**

Calculate based on:
- Sentiment (positive/neutral = higher score)
- Reach (follower count)
- Engagement rate
- Content relevance

**CRITICAL RULE: Official brand accounts MUST have partnership_score = 0**
- @nvidia, @NVIDIAGeForce, @NVIDIAAI = partnership_score: 0
- Partnership opportunities are for INDEPENDENT voices only

**Rising Star Detection:**
- engagement_rate > 2% AND followers < 50K
- Flag: is_rising_star = true

## Output Requirements

### JSON Schema

```json
{
  "reportType": "influencers",
  "brand": "NVIDIA",
  "period": {
    "days": 7,
    "startDate": "2025-01-06",
    "endDate": "2025-01-13"
  },
  "summary": {
    "headline": "Strong Analyst Coverage Drives NVIDIA Discussion",
    "insight": "Key insight about influencer landscape",
    "partnership_strategy": "2-3 sentences on recommended partnership approach",
    "risk_assessment": "Critical voices and potential PR risks to monitor"
  },
  "tier_counts": {
    "mega": 2,
    "macro": 8,
    "micro": 15,
    "nano": 25
  },
  "top_niches": ["Tech Analysis", "AI Research", "Trading", "News"],
  "influencers": [
    {
      "username": "@tech_analyst",
      "name": "Tech Analyst",
      "followers": 125000,
      "description": "Bio text here",
      "tier": "Macro",
      "voice_type": "analyst",
      "niche": "Tech Analysis",
      "sentiment": "positive",
      "partnership_score": 85,
      "is_rising_star": false,
      "engagement_rate": 1.5,
      "sample_tweet": {
        "text": "Actual tweet quote...",
        "likes": 500,
        "retweets": 50
      },
      "why_partner": "High reach analyst with positive stance on NVIDIA"
    }
  ],
  "partnership_opportunities": ["@analyst1", "@creator2", "@trader3"],
  "rising_stars": ["@rising1", "@rising2"],
  "critical_voices": ["@critic1", "@skeptic2"]
}
```

### HTML Report Output

Generate a standalone HTML report with:
- Tailwind CSS (CDN)
- Dark theme (slate-900 background)
- Tier distribution cards (Mega/Macro/Micro/Nano)
- Influencer cards with voice type badges
- Partnership opportunities section
- Rising stars section
- Critical voices section
- **REQUIRED FOOTER**: `Powered by XPOZ MCP Social Intelligence — visit xpoz.ai to see how you can use it` (with link to https://xpoz.ai)

## React Artifact Template

```jsx
import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Crown, Star, Sparkles, Circle, Users, TrendingUp, AlertTriangle, Handshake } from 'lucide-react';

export default function BrandInfluencers() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedTier, setSelectedTier] = useState('all');

  // CLAUDE: Replace with actual analyzed data
  const brand = 'NVIDIA';
  const period = { days: 7 };

  const summary = {
    headline: 'Strong Analyst Coverage Drives NVIDIA Discussion',
    insight: 'Tech analysts and traders dominate the conversation',
    partnership_strategy: 'Focus on Macro-tier analysts with positive sentiment...',
    risk_assessment: 'Monitor 3 critical voices raising valuation concerns'
  };

  const tierCounts = { mega: 2, macro: 8, micro: 15, nano: 25 };
  const topNiches = ['Tech Analysis', 'AI Research', 'Trading', 'News'];

  const influencers = [
    { username: '@tech_analyst', name: 'Tech Analyst', followers: 125000, tier: 'Macro', voice_type: 'analyst', niche: 'Tech Analysis', sentiment: 'positive', partnership_score: 85, is_rising_star: false, engagement_rate: 1.5 },
    { username: '@ai_investor', name: 'AI Investor', followers: 89000, tier: 'Micro', voice_type: 'trader', niche: 'AI Trading', sentiment: 'positive', partnership_score: 78, is_rising_star: false, engagement_rate: 2.1 },
    { username: '@chip_news', name: 'Chip News', followers: 450000, tier: 'Macro', voice_type: 'news', niche: 'Semiconductors', sentiment: 'neutral', partnership_score: 65, is_rising_star: false, engagement_rate: 0.8 },
    { username: '@nvidia', name: 'NVIDIA', followers: 2500000, tier: 'Mega', voice_type: 'official', niche: 'Official', sentiment: 'positive', partnership_score: 0, is_rising_star: false, engagement_rate: 0.5 },
    { username: '@rising_analyst', name: 'Rising Analyst', followers: 35000, tier: 'Micro', voice_type: 'analyst', niche: 'Tech Analysis', sentiment: 'positive', partnership_score: 72, is_rising_star: true, engagement_rate: 3.2 }
  ];

  const partnershipOpportunities = influencers.filter(i => i.partnership_score >= 70 && i.voice_type !== 'official');
  const risingStars = influencers.filter(i => i.is_rising_star);
  const criticalVoices = influencers.filter(i => ['negative', 'leaning_negative'].includes(i.sentiment));

  const tierStyles = {
    Mega: { color: 'from-purple-500 to-pink-500', bg: 'bg-purple-500/10', border: 'border-purple-500/20', text: 'text-purple-400', icon: Crown },
    Macro: { color: 'from-blue-500 to-cyan-500', bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-400', icon: Star },
    Micro: { color: 'from-emerald-500 to-teal-500', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', text: 'text-emerald-400', icon: Sparkles },
    Nano: { color: 'from-amber-500 to-orange-500', bg: 'bg-amber-500/10', border: 'border-amber-500/20', text: 'text-amber-400', icon: Circle }
  };

  const voiceTypeBadge = (type) => {
    const styles = {
      analyst: 'bg-blue-500/20 text-blue-400',
      trader: 'bg-green-500/20 text-green-400',
      news: 'bg-amber-500/20 text-amber-400',
      official: 'bg-purple-500/20 text-purple-400',
      researcher: 'bg-cyan-500/20 text-cyan-400',
      influencer: 'bg-pink-500/20 text-pink-400'
    };
    return styles[type] || styles.influencer;
  };

  const sentimentBadge = (s) => {
    const styles = {
      positive: 'bg-green-500/20 text-green-400',
      leaning_positive: 'bg-green-500/10 text-green-300',
      neutral: 'bg-gray-500/20 text-gray-400',
      leaning_negative: 'bg-red-500/10 text-red-300',
      negative: 'bg-red-500/20 text-red-400'
    };
    return styles[s] || styles.neutral;
  };

  const formatFollowers = (n) => n >= 1000000 ? (n/1000000).toFixed(1) + 'M' : n >= 1000 ? (n/1000).toFixed(0) + 'K' : n;

  const filteredInfluencers = selectedTier === 'all' ? influencers : influencers.filter(i => i.tier === selectedTier);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Users },
    { id: 'partnerships', label: 'Partnership Opportunities', icon: Handshake },
    { id: 'rising', label: 'Rising Stars', icon: TrendingUp },
    { id: 'critical', label: 'Critical Voices', icon: AlertTriangle }
  ];

  return (
    <div className="w-full max-w-5xl mx-auto p-6 bg-slate-900 rounded-xl text-white">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{brand} Influencer Discovery</h1>
          <p className="text-slate-400 text-sm">{influencers.length} influencers • {period.days} days</p>
        </div>
        <div className="flex gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-pink-400">{partnershipOpportunities.length}</div>
            <div className="text-xs text-slate-500">Opportunities</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-amber-400">{risingStars.length}</div>
            <div className="text-xs text-slate-500">Rising Stars</div>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-slate-800 rounded-lg p-4 mb-6">
        <h2 className="text-xl font-bold mb-2">{summary.headline}</h2>
        <p className="text-slate-300">{summary.insight}</p>
      </div>

      {/* Tier Distribution */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {Object.entries(tierCounts).map(([tier, count]) => {
          const style = tierStyles[tier.charAt(0).toUpperCase() + tier.slice(1)];
          const Icon = style?.icon || Circle;
          return (
            <div key={tier} className={`${style?.bg} rounded-lg p-4 ${style?.border} border`}>
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-5 h-5 ${style?.text}`} />
                <span className={`font-medium ${style?.text}`}>{tier.charAt(0).toUpperCase() + tier.slice(1)}</span>
              </div>
              <div className="text-3xl font-bold text-white">{count}</div>
            </div>
          );
        })}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-700 pb-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500/50'
                : 'text-slate-400 hover:bg-slate-800'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div>
          {/* Tier Filter */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setSelectedTier('all')}
              className={`px-3 py-1 rounded text-sm ${selectedTier === 'all' ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-400'}`}
            >
              All
            </button>
            {['Mega', 'Macro', 'Micro', 'Nano'].map(tier => (
              <button
                key={tier}
                onClick={() => setSelectedTier(tier)}
                className={`px-3 py-1 rounded text-sm ${selectedTier === tier ? 'bg-indigo-500 text-white' : 'bg-slate-800 text-slate-400'}`}
              >
                {tier}
              </button>
            ))}
          </div>

          {/* Influencer Grid */}
          <div className="grid grid-cols-2 gap-4">
            {filteredInfluencers.map((inf, i) => {
              const style = tierStyles[inf.tier];
              const Icon = style?.icon || Circle;
              return (
                <div key={i} className="bg-slate-800 rounded-lg p-4 relative">
                  {inf.partnership_score >= 70 && inf.voice_type !== 'official' && (
                    <div className="absolute -top-2 -right-2 bg-gradient-to-r from-green-500 to-teal-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                      {inf.partnership_score}
                    </div>
                  )}
                  <div className="flex items-start gap-3">
                    <div className={`w-10 h-10 rounded-full bg-gradient-to-br ${style?.color} flex items-center justify-center`}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{inf.name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${voiceTypeBadge(inf.voice_type)}`}>{inf.voice_type}</span>
                      </div>
                      <p className="text-slate-500 text-sm">{inf.username}</p>
                      <div className="flex items-center gap-3 mt-2 text-sm">
                        <span className="text-slate-400">{formatFollowers(inf.followers)}</span>
                        <span className={`px-2 py-0.5 rounded text-xs ${sentimentBadge(inf.sentiment)}`}>{inf.sentiment}</span>
                        {inf.is_rising_star && <span className="text-amber-400 text-xs">Rising Star</span>}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === 'partnerships' && (
        <div>
          <div className="bg-green-500/10 rounded-lg p-4 mb-4 border border-green-500/20">
            <h3 className="font-medium text-green-400 mb-2">Partnership Strategy</h3>
            <p className="text-slate-300 text-sm">{summary.partnership_strategy}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {partnershipOpportunities.map((inf, i) => (
              <div key={i} className="bg-slate-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">{inf.name}</span>
                  <span className="text-green-400 font-bold">{inf.partnership_score}/100</span>
                </div>
                <p className="text-slate-500 text-sm">{inf.username} • {formatFollowers(inf.followers)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'rising' && (
        <div className="grid grid-cols-2 gap-4">
          {risingStars.length > 0 ? risingStars.map((inf, i) => (
            <div key={i} className="bg-amber-500/10 rounded-lg p-4 border border-amber-500/20">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-amber-400" />
                <span className="font-medium">{inf.name}</span>
              </div>
              <p className="text-slate-500 text-sm">{inf.username}</p>
              <p className="text-amber-400 text-sm mt-2">{inf.engagement_rate.toFixed(1)}% engagement rate</p>
            </div>
          )) : <p className="text-slate-400 col-span-2">No rising stars detected in this period.</p>}
        </div>
      )}

      {activeTab === 'critical' && (
        <div>
          <div className="bg-red-500/10 rounded-lg p-4 mb-4 border border-red-500/20">
            <h3 className="font-medium text-red-400 mb-2">Risk Assessment</h3>
            <p className="text-slate-300 text-sm">{summary.risk_assessment}</p>
          </div>
          {criticalVoices.length > 0 ? (
            <div className="grid grid-cols-2 gap-4">
              {criticalVoices.map((inf, i) => (
                <div key={i} className="bg-slate-800 rounded-lg p-4 border border-red-500/20">
                  <span className="font-medium">{inf.name}</span>
                  <p className="text-slate-500 text-sm">{inf.username} • {formatFollowers(inf.followers)}</p>
                </div>
              ))}
            </div>
          ) : <p className="text-slate-400">No critical voices detected in this period.</p>}
        </div>
      )}
    </div>
  );
}
```

## Instructions for Claude

### CRITICAL REQUIREMENTS

1. **FETCH REAL USER DATA** - You MUST call `getTwitterUsersByKeywords` and fetch real users. Do NOT generate fake influencer data.

2. **USE EXPANDED QUERIES** - Always expand brand names to include ticker symbols.

3. **ASYNC POLLING** - Poll `checkOperationStatus` until status is "completed".

4. **OFFICIAL ACCOUNTS = 0 PARTNERSHIP SCORE** - Any account that is an official brand account (voice_type: "official") MUST have partnership_score = 0. These are not partnership opportunities.

5. **CALCULATE ENGAGEMENT RATE** - Use formula: (likes + retweets) / followers * 100

6. **DETECT RISING STARS** - Flag accounts with engagement_rate > 2% AND followers < 50K

### Voice Type Detection Rules

- **analyst**: Bio contains "analyst", "research", "analysis", financial credentials
- **trader**: Bio contains "trader", "trading", "options", "$" references
- **news**: Media outlet, journalist title, news organization
- **official**: Brand account, corporate account, verified brand
- **researcher**: PhD, professor, academic institution
- **influencer**: "creator", "content", large following without other signals
- **founder**: Bio contains "CEO", "founder", "co-founder", startup references
- **interviewer**: Bio contains "host", "podcast", "interviewer", media show references
- **community**: Fan accounts, community managers, enthusiast groups, unofficial fan pages

### Data Collection Steps

1. Accept brand name from user
2. Expand query with ticker symbol
3. Call `getTwitterUsersByKeywords` with expanded query
4. Poll `checkOperationStatus` until complete
5. Call `getTwitterPostsByKeywords` for sample tweets
6. Poll `checkOperationStatus` until complete
7. Classify each user by tier, voice type, sentiment
8. Calculate partnership scores (official = 0!)
9. Detect rising stars
10. Identify critical voices
11. Render React artifact with all categories
12. Generate standalone HTML report

### MCP Configuration

```
Endpoint: https://mcp.xpoz.ai/mcp
Transport: HTTP Streamable (not SSE)
Auth: Bearer Token
Tools: getTwitterUsersByKeywords, getTwitterPostsByKeywords, checkOperationStatus
```
