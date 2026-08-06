'use client';

import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { 
  BarChart3, 
  Calculator, 
  TrendingUp, 
  Globe, 
  Activity, 
  CheckCircle2, 
  AlertCircle,
  Layers,
  HelpCircle,
  FileSpreadsheet,
  Download
} from 'lucide-react';
import { toast } from 'sonner';

interface IndicatorInfo {
  code: string;
  name: string;
  unit: string;
  category: string;
  description: string;
}

interface CountryInfo {
  iso_code: string;
  name: string;
  region: string;
}

const DEFAULT_COUNTRIES = ['ZMB', 'KEN', 'NGA', 'ZAF', 'COD', 'UGA'];

export default function DHSDataLabPage() {
  const [activeTab, setActiveTab] = useState<'descriptive' | 'inferential' | 'regression'>('descriptive');
  const [metadata, setMetadata] = useState<{ indicators: IndicatorInfo[]; countries: CountryInfo[] } | null>(null);
  const [selectedCountries, setSelectedCountries] = useState<string[]>(['ZMB', 'KEN', 'NGA', 'ZAF']);
  const [selectedIndicatorX, setSelectedIndicatorX] = useState<string>('u5_mortality');
  const [selectedIndicatorY, setSelectedIndicatorY] = useState<string>('stunting_prevalence');
  const [selectedTestType, setSelectedTestType] = useState<string>('t_test');

  const [descriptiveData, setDescriptiveData] = useState<any>(null);
  const [inferentialData, setInferentialData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // Load datasets metadata
  useEffect(() => {
    fetch('/api/v1/dhs/datasets')
      .then(res => res.json())
      .then(data => setMetadata(data))
      .catch(() => {
        // Fallback metadata if API route is proxied or static
        setMetadata({
          indicators: [
            { code: 'u5_mortality', name: 'Under-5 Mortality Rate', unit: 'per 1k live births', category: 'Child Health', description: 'Probability of dying under 5 years.' },
            { code: 'stunting_prevalence', name: 'Stunting Prevalence (U5)', unit: '%', category: 'Nutrition', description: 'Percentage of children under 5 with height-for-age < -2 SD.' },
            { code: 'full_immunization', name: 'Full Immunization Coverage', unit: '%', category: 'Immunization', description: 'Children 12-23m with all WHO basic vaccines.' },
            { code: 'anc4_coverage', name: 'Antenatal Care 4+ Visits', unit: '%', category: 'Maternal Health', description: 'Women with 4+ ANC visits during pregnancy.' },
            { code: 'malaria_prevalence_u5', name: 'Malaria Parasitemia (U5)', unit: '%', category: 'Infectious Diseases', description: 'Percentage of children 6-59m testing positive for malaria.' },
            { code: 'maternal_mortality_ratio', name: 'Maternal Mortality Ratio', unit: 'per 100k live births', category: 'Maternal Health', description: 'Maternal deaths per 100k live births.' }
          ],
          countries: [
            { iso_code: 'ZMB', name: 'Zambia', region: 'Southern Africa' },
            { iso_code: 'KEN', name: 'Kenya', region: 'East Africa' },
            { iso_code: 'NGA', name: 'Nigeria', region: 'West Africa' },
            { iso_code: 'ZAF', name: 'South Africa', region: 'Southern Africa' },
            { iso_code: 'COD', name: 'DR Congo', region: 'Central Africa' },
            { iso_code: 'UGA', name: 'Uganda', region: 'East Africa' },
            { iso_code: 'ETH', name: 'Ethiopia', region: 'East Africa' },
            { iso_code: 'GHA', name: 'Ghana', region: 'West Africa' }
          ]
        });
      });
  }, []);

  // Fetch descriptive stats
  const loadDescriptiveStats = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/dhs/descriptive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          country_codes: selectedCountries,
          indicator: selectedIndicatorX
        })
      });
      const data = await res.json();
      setDescriptiveData(data);
    } catch (err) {
      toast.error('Failed to load descriptive statistics');
    } finally {
      setLoading(false);
    }
  };

  // Fetch inferential stats
  const loadInferentialStats = async (testTypeOverride?: string) => {
    setLoading(true);
    const testToRun = testTypeOverride || selectedTestType;
    try {
      const res = await fetch('/api/v1/dhs/inferential', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          test_type: testToRun,
          country_codes: selectedCountries,
          indicator_x: selectedIndicatorX,
          indicator_y: selectedIndicatorY
        })
      });
      const data = await res.json();
      setInferentialData(data);
      toast.success(`Executed ${testToRun.toUpperCase()} test analysis`);
    } catch (err) {
      toast.error('Failed to execute inferential test');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'descriptive') {
      loadDescriptiveStats();
    } else {
      loadInferentialStats(activeTab === 'regression' ? 'linear_regression' : selectedTestType);
    }
  }, [selectedCountries, selectedIndicatorX, selectedIndicatorY, activeTab, selectedTestType]);

  const toggleCountry = (iso: string) => {
    if (selectedCountries.includes(iso)) {
      if (selectedCountries.length <= 1) {
        toast.warning('Select at least one country');
        return;
      }
      setSelectedCountries(selectedCountries.filter(c => c !== iso));
    } else {
      setSelectedCountries([...selectedCountries, iso]);
    }
  };

  // ECharts Options
  const getDescriptiveBarOption = () => {
    if (!descriptiveData || !descriptiveData.per_country) return {};
    const countries = Object.keys(descriptiveData.per_country);
    const means = countries.map(c => descriptiveData.per_country[c].mean);
    const medians = countries.map(c => descriptiveData.per_country[c].median);
    const names = countries.map(c => descriptiveData.per_country[c].country_name);

    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { textStyle: { color: '#9ca3af' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: names, axisLabel: { color: '#9ca3af' } },
      yAxis: { type: 'value', axisLabel: { color: '#9ca3af' } },
      series: [
        { name: 'Mean', type: 'bar', data: means, itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] } },
        { name: 'Median', type: 'bar', data: medians, itemStyle: { color: '#10b981', borderRadius: [4, 4, 0, 0] } }
      ]
    };
  };

  const getScatterRegressionOption = () => {
    if (!inferentialData || !inferentialData.summary || !inferentialData.summary.scatter_points) return {};
    const pts = inferentialData.summary.scatter_points;
    const trend = inferentialData.summary.trend_line || [];

    const scatterSeriesData = pts.map((p: any) => [p.x, p.y]);
    const lineSeriesData = trend.map((t: any) => [t.x, t.y]);

    return {
      tooltip: { trigger: 'item', formatter: (params: any) => `X: ${params.value[0]}, Y: ${params.value[1]}` },
      legend: { textStyle: { color: '#9ca3af' } },
      xAxis: { name: descriptiveData?.indicator_meta?.name || 'Indicator X', type: 'value', axisLabel: { color: '#9ca3af' } },
      yAxis: { name: 'Indicator Y', type: 'value', axisLabel: { color: '#9ca3af' } },
      series: [
        { name: 'DHS Samples', type: 'scatter', data: scatterSeriesData, itemStyle: { color: '#8b5cf6' } },
        { name: 'OLS Trendline', type: 'line', data: lineSeriesData, lineStyle: { color: '#ef4444', width: 3 } }
      ]
    };
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      {/* Top Header */}
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-2 text-blue-400 font-semibold text-sm uppercase tracking-wider mb-1">
              <Calculator className="w-4 h-4" /> EpiSphere Health Data Lab
            </div>
            <h1 className="text-3xl font-bold text-slate-100 tracking-tight">
              DHS Multi-Country Analytics & Inferential Statistics
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Statistical descriptives, boxplot distributions, hypothesis testing (T-Test, ANOVA, Mann-Whitney), & OLS regression for Demographic & Health Surveys.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => toast.success('Exporting DHS statistical report...')}
              className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-lg border border-slate-700 transition"
            >
              <Download className="w-4 h-4" /> Export Report
            </button>
          </div>
        </div>

        {/* Global Controls Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            {/* Country Selector Badges */}
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Evaluated DHS Countries ({selectedCountries.length} selected)
              </label>
              <div className="flex flex-wrap gap-2">
                {metadata?.countries.map(c => {
                  const isSelected = selectedCountries.includes(c.iso_code);
                  return (
                    <button
                      key={c.iso_code}
                      onClick={() => toggleCountry(c.iso_code)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition ${
                        isSelected 
                          ? 'bg-blue-600/30 text-blue-400 border border-blue-500/50' 
                          : 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-750'
                      }`}
                    >
                      <Globe className="w-3.5 h-3.5" />
                      {c.name} ({c.iso_code})
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Indicator Selectors */}
            <div className="flex flex-wrap items-center gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Primary Indicator (X)
                </label>
                <select
                  value={selectedIndicatorX}
                  onChange={(e) => setSelectedIndicatorX(e.target.value)}
                  className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
                >
                  {metadata?.indicators.map(ind => (
                    <option key={ind.code} value={ind.code}>{ind.name}</option>
                  ))}
                </select>
              </div>

              {activeTab === 'regression' && (
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    Secondary Indicator (Y)
                  </label>
                  <select
                    value={selectedIndicatorY}
                    onChange={(e) => setSelectedIndicatorY(e.target.value)}
                    className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    {metadata?.indicators.map(ind => (
                      <option key={ind.code} value={ind.code}>{ind.name}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex border-b border-slate-800 space-x-6">
          <button
            onClick={() => setActiveTab('descriptive')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'descriptive'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <BarChart3 className="w-4 h-4" /> Descriptive Statistics & Profiles
          </button>
          <button
            onClick={() => setActiveTab('inferential')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'inferential'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Calculator className="w-4 h-4" /> Inferential Hypothesis Workbench
          </button>
          <button
            onClick={() => setActiveTab('regression')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition ${
              activeTab === 'regression'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <TrendingUp className="w-4 h-4" /> Correlation & OLS Regression
          </button>
        </div>

        {/* TAB 1: DESCRIPTIVE STATISTICS */}
        {activeTab === 'descriptive' && descriptiveData && (
          <div className="space-y-6">
            {/* Top Metric Cards Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-slate-400 text-xs font-medium">Pooled Mean</span>
                <p className="text-2xl font-bold text-blue-400 mt-1">{descriptiveData.pooled_stats?.mean}</p>
                <span className="text-xs text-slate-500">95% CI: [{descriptiveData.pooled_stats?.ci_95?.[0]}, {descriptiveData.pooled_stats?.ci_95?.[1]}]</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-slate-400 text-xs font-medium">Median</span>
                <p className="text-2xl font-bold text-emerald-400 mt-1">{descriptiveData.pooled_stats?.median}</p>
                <span className="text-xs text-slate-500">Q25: {descriptiveData.pooled_stats?.q25} | Q75: {descriptiveData.pooled_stats?.q75}</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-slate-400 text-xs font-medium">Std Deviation</span>
                <p className="text-2xl font-bold text-purple-400 mt-1">{descriptiveData.pooled_stats?.std_dev}</p>
                <span className="text-xs text-slate-500">Variance: {descriptiveData.pooled_stats?.variance}</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-slate-400 text-xs font-medium">Interquartile Range (IQR)</span>
                <p className="text-2xl font-bold text-amber-400 mt-1">{descriptiveData.pooled_stats?.iqr}</p>
                <span className="text-xs text-slate-500">Range: {descriptiveData.pooled_stats?.min} - {descriptiveData.pooled_stats?.max}</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-slate-400 text-xs font-medium">Skewness</span>
                <p className="text-2xl font-bold text-sky-400 mt-1">{descriptiveData.pooled_stats?.skewness}</p>
                <span className="text-xs text-slate-500">Kurtosis: {descriptiveData.pooled_stats?.kurtosis}</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-slate-400 text-xs font-medium">Total Samples</span>
                <p className="text-2xl font-bold text-slate-100 mt-1">{descriptiveData.pooled_stats?.count}</p>
                <span className="text-xs text-slate-500">N per country = 30</span>
              </div>
            </div>

            {/* ECharts Visualization */}
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-2">
              <h3 className="text-lg font-semibold text-slate-200">
                Country Mean & Median Comparison
              </h3>
              <p className="text-slate-400 text-xs mb-4">
                Comparison of central tendency metrics for {descriptiveData.indicator_meta?.name} ({descriptiveData.indicator_meta?.unit}).
              </p>
              <ReactECharts option={getDescriptiveBarOption()} style={{ height: '350px' }} />
            </div>

            {/* Comprehensive Table */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4 text-blue-400" /> Per-Country Descriptive Parameter Table
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 uppercase text-xs">
                    <tr>
                      <th className="p-3">Country</th>
                      <th className="p-3">N</th>
                      <th className="p-3">Mean</th>
                      <th className="p-3">95% CI</th>
                      <th className="p-3">Median</th>
                      <th className="p-3">Std Dev</th>
                      <th className="p-3">IQR</th>
                      <th className="p-3">Min / Max</th>
                      <th className="p-3">Skewness</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {Object.keys(descriptiveData.per_country || {}).map(iso => {
                      const item = descriptiveData.per_country[iso];
                      return (
                        <tr key={iso} className="hover:bg-slate-800/50">
                          <td className="p-3 font-semibold text-slate-100">{item.country_name} ({iso})</td>
                          <td className="p-3">{item.count}</td>
                          <td className="p-3 font-bold text-blue-400">{item.mean}</td>
                          <td className="p-3 text-slate-400">[{item.ci_95[0]}, {item.ci_95[1]}]</td>
                          <td className="p-3 text-emerald-400 font-medium">{item.median}</td>
                          <td className="p-3">{item.std_dev}</td>
                          <td className="p-3">{item.iqr}</td>
                          <td className="p-3">{item.min} / {item.max}</td>
                          <td className="p-3">{item.skewness}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: INFERENTIAL HYPOTHESIS WORKBENCH */}
        {activeTab === 'inferential' && (
          <div className="space-y-6">
            {/* Test Selector Buttons */}
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl space-y-3">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                Select Inferential Statistical Test
              </label>
              <div className="flex flex-wrap gap-2">
                {[
                  { type: 't_test', label: "Independent T-Test" },
                  { type: 'welch_t_test', label: "Welch's T-Test (Unequal Var)" },
                  { type: 'mann_whitney', label: "Mann-Whitney U Test" },
                  { type: 'anova', label: "One-Way ANOVA (F-Test)" },
                  { type: 'chi_square', label: "Chi-Square Test" }
                ].map(t => (
                  <button
                    key={t.type}
                    onClick={() => {
                      setSelectedTestType(t.type);
                      loadInferentialStats(t.type);
                    }}
                    className={`px-4 py-2 rounded-lg text-xs font-semibold transition ${
                      selectedTestType === t.type
                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-750'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Test Output Results Card */}
            {inferentialData && inferentialData.summary && (
              <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-6">
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                      <Calculator className="w-5 h-5 text-blue-400" />
                      {inferentialData.summary.test_name}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Evaluated on {selectedIndicatorX} indicator across {selectedCountries.join(', ')}.
                    </p>
                  </div>
                  <div>
                    {inferentialData.summary.significant_95 ? (
                      <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 text-xs font-semibold rounded-full flex items-center gap-1.5">
                        <CheckCircle2 className="w-4 h-4" /> Statistically Significant (p &lt; 0.05)
                      </span>
                    ) : (
                      <span className="px-3 py-1 bg-amber-500/20 text-amber-400 border border-amber-500/40 text-xs font-semibold rounded-full flex items-center gap-1.5">
                        <AlertCircle className="w-4 h-4" /> Not Significant (p &ge; 0.05)
                      </span>
                    )}
                  </div>
                </div>

                {/* Key Stat Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {inferentialData.summary.t_statistic !== undefined && (
                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400">t-Statistic</span>
                      <p className="text-2xl font-bold text-blue-400 mt-1">{inferentialData.summary.t_statistic}</p>
                    </div>
                  )}
                  {inferentialData.summary.u_statistic !== undefined && (
                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400">U-Statistic</span>
                      <p className="text-2xl font-bold text-purple-400 mt-1">{inferentialData.summary.u_statistic}</p>
                    </div>
                  )}
                  {inferentialData.summary.f_statistic !== undefined && (
                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400">F-Statistic</span>
                      <p className="text-2xl font-bold text-sky-400 mt-1">{inferentialData.summary.f_statistic}</p>
                    </div>
                  )}
                  {inferentialData.summary.chi2_statistic !== undefined && (
                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400">Chi-Square (χ²)</span>
                      <p className="text-2xl font-bold text-amber-400 mt-1">{inferentialData.summary.chi2_statistic}</p>
                    </div>
                  )}

                  <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                    <span className="text-xs text-slate-400">p-Value</span>
                    <p className={`text-2xl font-bold mt-1 ${inferentialData.summary.significant_95 ? 'text-emerald-400' : 'text-slate-200'}`}>
                      {inferentialData.summary.p_value}
                    </p>
                  </div>

                  {inferentialData.summary.degrees_freedom !== undefined && (
                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400">Degrees of Freedom</span>
                      <p className="text-2xl font-bold text-slate-300 mt-1">{inferentialData.summary.degrees_freedom}</p>
                    </div>
                  )}

                  {inferentialData.summary.cohens_d !== undefined && (
                    <div className="bg-slate-950 p-4 rounded-lg border border-slate-800">
                      <span className="text-xs text-slate-400">Effect Size (Cohen&apos;s d)</span>
                      <p className="text-2xl font-bold text-pink-400 mt-1">{inferentialData.summary.cohens_d}</p>
                    </div>
                  )}
                </div>

                {/* Interpretation Note */}
                <div className="bg-slate-950/80 border border-slate-800 p-4 rounded-lg flex items-start gap-3">
                  <HelpCircle className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-slate-200">Epidemiological Interpretation</h4>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                      {inferentialData.summary.interpretation}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 3: CORRELATION & OLS REGRESSION */}
        {activeTab === 'regression' && inferentialData && inferentialData.summary && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-xs text-slate-400 font-medium">Pearson Correlation (r)</span>
                <p className="text-2xl font-bold text-purple-400 mt-1">{inferentialData.summary.pearson_r}</p>
                <span className="text-xs text-slate-500">p = {inferentialData.summary.pearson_p_value}</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-xs text-slate-400 font-medium">Spearman Rank (ρ)</span>
                <p className="text-2xl font-bold text-indigo-400 mt-1">{inferentialData.summary.spearman_r}</p>
                <span className="text-xs text-slate-500">p = {inferentialData.summary.spearman_p_value}</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-xs text-slate-400 font-medium">R-Squared (R²)</span>
                <p className="text-2xl font-bold text-emerald-400 mt-1">{inferentialData.summary.r_squared}</p>
                <span className="text-xs text-slate-500">Variance Explained</span>
              </div>

              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <span className="text-xs text-slate-400 font-medium">OLS Slope</span>
                <p className="text-2xl font-bold text-amber-400 mt-1">{inferentialData.summary.ols_slope}</p>
                <span className="text-xs text-slate-500">Intercept: {inferentialData.summary.ols_intercept}</span>
              </div>
            </div>

            {/* Scatter & Regression Line Chart */}
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-2">
              <h3 className="text-lg font-semibold text-slate-200">
                Ordinary Least Squares (OLS) Regression Scatter Plot
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Bivariate regression relationship between {selectedIndicatorX} and {selectedIndicatorY}.
              </p>
              <ReactECharts option={getScatterRegressionOption()} style={{ height: '400px' }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
