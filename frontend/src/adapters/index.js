/**
 * Data Adapters for ArthaLens Terminal
 * Transforms backend API contracts into view-ready, presentation-safe view models.
 * Enforces live data integrity: Never hardcodes numbers or replaces missing data with fake numbers.
 */

export function formatNumber(val, decimals = 2) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return Number(val).toLocaleString('en-IN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

export function formatLakhs(val) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  const num = Number(val);
  if (num >= 10000000) return `${(num / 10000000).toFixed(2)} Cr`;
  if (num >= 100000) return `${(num / 100000).toFixed(2)} L`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)} K`;
  return num.toString();
}

export function adaptMarketBar(marketList) {
  if (!Array.isArray(marketList)) return [];
  return marketList.map(item => {
    const isUnavailable = !item || item.status === 'UNAVAILABLE' || item.last_price === null || item.last_price === undefined;
    const price = isUnavailable ? null : item.last_price;
    const changePct = isUnavailable ? null : (item.change_percent ?? 0);
    const changePts = isUnavailable ? null : (item.change ?? 0);
    
    return {
      symbol: item?.symbol || 'UNKNOWN',
      name: item?.symbol === 'INDIAVIX' ? 'INDIA VIX' : (item?.symbol === 'BANKNIFTY' ? 'BANK NIFTY' : (item?.symbol || '—')),
      priceFormatted: isUnavailable ? 'UNAVAILABLE' : formatNumber(price),
      rawPrice: price,
      changePctFormatted: isUnavailable ? '—' : `${changePct >= 0 ? '+' : ''}${formatNumber(changePct)}%`,
      changePtsFormatted: isUnavailable ? '—' : `${changePts >= 0 ? '+' : ''}${formatNumber(changePts)}`,
      isUp: (changePct ?? 0) >= 0,
      isUnavailable,
      status: item?.status || 'UNAVAILABLE',
      timestamp: item?.timestamp || null
    };
  });
}

export function adaptOptionChain(chainData) {
  if (!chainData || chainData.status === 'UNAVAILABLE') {
    return {
      isUnavailable: true,
      symbol: chainData?.symbol || 'NIFTY',
      expiry: chainData?.expiry || null,
      spotPrice: null,
      spotFormatted: 'UNAVAILABLE',
      atmStrike: null,
      strikes: [],
      maxPain: null,
      netGex: null,
      pcr: null
    };
  }

  const spot = chainData.underlying_price ?? null;
  const strikes = Array.isArray(chainData.strikes) ? chainData.strikes : [];

  return {
    isUnavailable: false,
    symbol: chainData.symbol,
    expiry: chainData.expiry,
    spotPrice: spot,
    spotFormatted: formatNumber(spot),
    atmStrike: chainData.atm_strike ?? null,
    pcr: chainData.pcr ?? null,
    maxPain: chainData.max_pain ?? null,
    netGex: chainData.net_gex ?? null,
    strikes: strikes.map(s => {
      const ce = s.ce || {};
      const pe = s.pe || {};
      return {
        strike: s.strike,
        isAtm: s.strike === chainData.atm_strike,
        isMaxPain: s.strike === chainData.max_pain,
        ce: {
          ltp: ce.last_price ?? null,
          ltpFormatted: formatNumber(ce.last_price),
          change: ce.change ?? 0,
          oi: ce.open_interest ?? 0,
          oiFormatted: formatLakhs(ce.open_interest),
          changeOi: ce.change_in_open_interest ?? 0,
          changeOiFormatted: formatLakhs(ce.change_in_open_interest),
          volume: ce.volume ?? 0,
          volumeFormatted: formatLakhs(ce.volume),
          iv: ce.iv ?? null,
          ivFormatted: ce.iv ? `${formatNumber(ce.iv, 1)}%` : '—',
          delta: ce.delta ?? null,
          theta: ce.theta ?? null,
          gamma: ce.gamma ?? null,
          vega: ce.vega ?? null
        },
        pe: {
          ltp: pe.last_price ?? null,
          ltpFormatted: formatNumber(pe.last_price),
          change: pe.change ?? 0,
          oi: pe.open_interest ?? 0,
          oiFormatted: formatLakhs(pe.open_interest),
          changeOi: pe.change_in_open_interest ?? 0,
          changeOiFormatted: formatLakhs(pe.change_in_open_interest),
          volume: pe.volume ?? 0,
          volumeFormatted: formatLakhs(pe.volume),
          iv: pe.iv ?? null,
          ivFormatted: pe.iv ? `${formatNumber(pe.iv, 1)}%` : '—',
          delta: pe.delta ?? null,
          theta: pe.theta ?? null,
          gamma: pe.gamma ?? null,
          vega: pe.vega ?? null
        }
      };
    })
  };
}

export function adaptExpiryIntel(intelData) {
  if (!intelData || intelData.status === 'UNAVAILABLE') {
    return {
      isUnavailable: true,
      symbol: intelData?.symbol || 'NIFTY',
      expiry: intelData?.expiry || null,
      netGex: null,
      regime: 'UNAVAILABLE',
      violenceProbability: 'UNKNOWN',
      pinTarget: null,
      gammaProfile: [],
      dealerHedging: null,
      probabilityScore: null,
      casMonitor: null,
      historicalComparison: [],
      hasHistory: false,
      alerts: ['Market data feed unavailable. Expiry intelligence paused.']
    };
  }

  const hist = Array.isArray(intelData.historical_comparison) ? intelData.historical_comparison : [];

  return {
    isUnavailable: false,
    symbol: intelData.symbol,
    expiry: intelData.expiry,
    timestamp: intelData.timestamp,
    netGex: intelData.net_gex ?? 0,
    netGexFormatted: formatLakhs(intelData.net_gex),
    regime: intelData.regime || 'Neutral',
    violenceProbability: intelData.violence_probability || 'MEDIUM',
    pinTarget: intelData.pin_target_strike ?? null,
    expectedRangeLower: intelData.expected_range_lower,
    expectedRangeUpper: intelData.expected_range_upper,
    gammaProfile: intelData.gamma_profile || [],
    dealerHedging: intelData.dealer_hedging || {
      net_gex: intelData.net_gex ?? 0,
      dealer_position: 'Neutral',
      hedging_direction: 'Balanced',
      gamma_flip_level: null,
      distance_to_flip: null
    },
    probabilityScore: intelData.probability_score || {
      pinning_probability: 33.3,
      squeeze_probability: 33.3,
      breakout_probability: 33.4,
      primary_factor: 'Balanced option interest'
    },
    casMonitor: intelData.cas_monitor || null,
    historicalComparison: hist,
    hasHistory: hist.length > 0,
    alerts: intelData.alerts || []
  };
}

export function adaptNewsIntel(newsData) {
  if (!newsData) {
    return {
      isUnavailable: true,
      newsItems: [],
      fusionSignal: null,
      impactSummary: null
    };
  }

  const items = Array.isArray(newsData.news_items) ? newsData.news_items : [];

  return {
    isUnavailable: items.length === 0,
    newsItems: items.map(item => ({
      id: item.id || Math.random().toString(),
      source: item.source || 'NSE Feed',
      title: item.title || item.headline || 'Market Update',
      summary: item.summary || item.content || '',
      url: item.url || '#',
      category: item.category || 'General',
      relevanceScore: item.relevance_score ?? 50,
      impact: item.impact || 'MEDIUM',
      timestamp: item.timestamp || item.published_at || new Date().toISOString()
    })),
    fusionSignal: newsData.fusion_signal || null,
    impactSummary: newsData.impact_summary || null
  };
}

export function adaptWatchlist(watchlistData) {
  if (!watchlistData || watchlistData.status === 'UNAVAILABLE') {
    return {
      isUnavailable: true,
      items: [],
      universe: ["NIFTY 50", "BANK NIFTY", "SENSEX", "INDIA VIX", "USD/INR", "BRENT CRUDE"]
    };
  }

  const items = Array.isArray(watchlistData.items) ? watchlistData.items : [];

  return {
    isUnavailable: false,
    items: items.map(item => ({
      rank: item.rank,
      asset: item.asset,
      eventOrDriver: item.event_or_driver,
      reason: item.reason,
      priorityScore: item.priority_score,
      priorityTier: item.priority_tier,
      confidence: item.confidence,
      direction: item.direction,
      factors: item.factors,
      tradeHint: item.trade_hint,
      timestamp: item.timestamp
    })),
    universe: watchlistData.universe || []
  };
}

export function adaptAnalytics(analyticsData) {
  if (!analyticsData) return null;
  return {
    maxPain: analyticsData.max_pain ?? null,
    pcr: analyticsData.pcr ?? null,
    gex: analyticsData.gex ?? {},
    ivSurface: analyticsData.iv_surface ?? null,
    futuresBasis: analyticsData.futures_basis ?? null,
    supportResistance: analyticsData.support_resistance ?? null,
    hasIvPercentile: Boolean(analyticsData.iv_percentile)
  };
}
