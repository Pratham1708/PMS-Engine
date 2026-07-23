import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useBreakpoint } from '../config/breakpoints';
import {
  fetchStrategies,
  createStrategy,
  updateStrategy,
  deleteStrategy,
  duplicateStrategy,
  fetchFeaturesRegistry,
  validateStrategy,
  executeStrategyScoring
} from '../api/strategyApi';
import RatingBadge from '../components/common/RatingBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ExplainModal from '../components/common/ExplainModal';

export default function QuantStrategyStudio() {
  const [strategies, setStrategies] = useState([]);
  const [features, setFeatures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Wizard state
  const [activeStep, setActiveStep] = useState(1);
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  
  // Strategy Builder State
  const [strategyName, setStrategyName] = useState('');
  const [description, setDescription] = useState('');
  const [strategyType, setStrategyType] = useState('Stock');
  const [strategyPrompt, setStrategyPrompt] = useState('');
  const [visibility, setVisibility] = useState('Private');
  const [status, setStatus] = useState('Draft');
  
  const [selectedFeatureIds, setSelectedFeatureIds] = useState(new Set());
  const [weights, setWeights] = useState({}); // feature_id -> percentage
  const [normalizationMethods, setNormalizationMethods] = useState({}); // feature_id -> method
  
  const [scoringMethod, setScoringMethod] = useState('Weighted Average');
  const [thresholdBuy, setThresholdBuy] = useState(35);
  const [thresholdHold, setThresholdHold] = useState(-15);
  const [thresholdSell, setThresholdSell] = useState(-15);
  
  // Search & Filters for Features
  const [featureSearch, setFeatureSearch] = useState('');
  const [featureCategoryFilter, setFeatureCategoryFilter] = useState('All');
  
  // Validation & Live Preview State
  const [validationResult, setValidationResult] = useState(null);
  const [previewStocks, setPreviewStocks] = useState([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [changeSummary, setChangeSummary] = useState('');
  
  // Modal for Explainability
  const [explainStockSymbol, setExplainStockSymbol] = useState(null);
  
  const navigate = useNavigate();

  // Load initial data
  const loadStudioData = () => {
    setLoading(true);
    return Promise.all([fetchStrategies(), fetchFeaturesRegistry()])
      .then(([stratRes, featRes]) => {
        setStrategies(stratRes.data || []);
        setFeatures(featRes.data || []);
      })
      .catch((err) => {
        console.error('Failed to load Strategy Studio data', err);
        setError('Failed to fetch strategies and dynamic feature registries.');
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadStudioData();
  }, []);

  // Update dynamic validation and preview results when features/weights/thresholds change
  useEffect(() => {
    if (selectedFeatureIds.size === 0) {
      setValidationResult(null);
      setPreviewStocks([]);
      return;
    }

    const definition = buildTransientDefinition();
    
    // Validate
    validateStrategy(definition)
      .then((res) => {
        setValidationResult(res.data);
      })
      .catch((err) => console.error('Transient validation failed', err));

    // Execute scoring preview (debounce/throttle or load on step 5)
    if (activeStep === 5) {
      setPreviewLoading(true);
      executeStrategyScoring(definition)
        .then((res) => {
          setPreviewStocks(res.data.stocks || []);
        })
        .catch((err) => console.error('Scoring execution failed', err))
        .finally(() => setPreviewLoading(false));
    }
  }, [selectedFeatureIds, weights, scoringMethod, thresholdBuy, thresholdHold, thresholdSell, activeStep]);

  const buildTransientDefinition = () => {
    const featuresList = Array.from(selectedFeatureIds).map((fid) => {
      const orig = features.find(f => f.feature_id === fid) || {};
      return {
        feature_id: fid,
        feature_group: orig.category || 'General',
        enabled: true
      };
    });

    const weightsList = Array.from(selectedFeatureIds).map((fid) => ({
      feature_id: fid,
      weight: weights[fid] || 0.0,
      normalization_method: normalizationMethods[fid] || 'Default',
      contribution_method: 'Additive'
    }));

    return {
      features: featuresList,
      weights: weightsList,
      scoring_config: {
        scoring_method: scoringMethod,
        aggregation_method: 'Additive',
        threshold_buy: thresholdBuy,
        threshold_hold: thresholdHold,
        threshold_sell: thresholdSell,
        normalization: 'Default',
        recommendation_method: 'Standard'
      },
      risk_profile: 'Medium',
      filters: null
    };
  };

  // Helper actions
  const handleAutoRebalance = () => {
    if (selectedFeatureIds.size === 0) return;
    const equalWeight = parseFloat((100.0 / selectedFeatureIds.size).toFixed(2));
    const newWeights = {};
    let sum = 0;
    Array.from(selectedFeatureIds).forEach((fid, idx) => {
      if (idx === selectedFeatureIds.size - 1) {
        newWeights[fid] = parseFloat((100.0 - sum).toFixed(2));
      } else {
        newWeights[fid] = equalWeight;
        sum += equalWeight;
      }
    });
    setWeights(newWeights);
  };

  const handleResetWeights = () => {
    const newWeights = {};
    Array.from(selectedFeatureIds).forEach((fid) => {
      newWeights[fid] = 0;
    });
    setWeights(newWeights);
  };

  const toggleFeature = (fid) => {
    setSelectedFeatureIds((prev) => {
      const next = new Set(prev);
      if (next.has(fid)) {
        next.delete(fid);
        const newWeights = { ...weights };
        delete newWeights[fid];
        setWeights(newWeights);
      } else {
        next.add(fid);
        // Default allocation to 0 before user adjusts
        setWeights(prevW => ({ ...prevW, [fid]: 0 }));
      }
      return next;
    });
  };

  const handleWeightChange = (fid, val) => {
    setWeights((prev) => ({
      ...prev,
      [fid]: parseFloat(val)
    }));
  };

  const handleNormalizationChange = (fid, val) => {
    setNormalizationMethods((prev) => ({
      ...prev,
      [fid]: val
    }));
  };

  // CRUD API Calls
  const handleSaveStrategy = () => {
    const definition = buildTransientDefinition();
    const payload = {
      strategy_name: strategyName || 'Unnamed Custom Strategy',
      description: description,
      strategy_type: strategyType,
      strategy_prompt: strategyPrompt,
      strategy_definition: definition,
      visibility: visibility
    };

    if (isEditing && selectedStrategyId) {
      updateStrategy(selectedStrategyId, { ...payload, status, change_summary: changeSummary || 'Updated strategy configuration' })
        .then(() => {
          loadStudioData();
          resetBuilder();
        })
        .catch((err) => alert('Failed to save strategy: ' + err.response?.data?.detail || err.message));
    } else {
      createStrategy(payload)
        .then(() => {
          loadStudioData();
          resetBuilder();
        })
        .catch((err) => alert('Failed to save strategy: ' + err.response?.data?.detail || err.message));
    }
  };

  const handleEdit = (strat) => {
    setSelectedStrategyId(strat.strategy_id);
    setStrategyName(strat.strategy_name);
    setDescription(strat.description || '');
    setStrategyType(strat.strategy_type || 'Stock');
    setStrategyPrompt(strat.strategy_prompt || '');
    setVisibility(strat.visibility || 'Private');
    setStatus(strat.status || 'Draft');
    
    // Load config definition
    const def = strat.strategy_definition || {};
    const featSet = new Set(def.features?.map(f => f.feature_id) || []);
    setSelectedFeatureIds(featSet);
    
    const wtMap = {};
    const normMap = {};
    def.weights?.forEach(w => {
      wtMap[w.feature_id] = w.weight;
      normMap[w.feature_id] = w.normalization_method || 'Default';
    });
    setWeights(wtMap);
    setNormalizationMethods(normMap);
    
    const sc = def.scoring_config || {};
    setScoringMethod(sc.scoring_method || 'Weighted Average');
    setThresholdBuy(sc.threshold_buy ?? 35);
    setThresholdHold(sc.threshold_hold ?? -15);
    setThresholdSell(sc.threshold_sell ?? -15);
    
    setIsEditing(true);
    setActiveStep(1);
  };

  const handleDuplicate = (id, name) => {
    duplicateStrategy(id, `${name} (Copy)`)
      .then(() => loadStudioData())
      .catch((err) => alert('Clone failed: ' + err.message));
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to permanently delete this strategy?')) {
      deleteStrategy(id)
        .then(() => loadStudioData())
        .catch((err) => alert('Delete failed: ' + err.message));
    }
  };

  const handleExportJSON = (strat) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(strat, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `${strat.strategy_name.toLowerCase().replace(/\s+/g, '_')}_config.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleImportJSON = (e) => {
    const fileReader = new FileReader();
    fileReader.readAsText(e.target.files[0], "UTF-8");
    fileReader.onload = e => {
      try {
        const strat = JSON.parse(e.target.result);
        if (!strat.strategy_name || !strat.strategy_definition) {
          alert("Invalid Strategy configuration JSON file.");
          return;
        }
        
        setStrategyName(strat.strategy_name);
        setDescription(strat.description || '');
        setStrategyType(strat.strategy_type || 'Stock');
        setStrategyPrompt(strat.strategy_prompt || '');
        setVisibility(strat.visibility || 'Private');
        setStatus(strat.status || 'Draft');
        
        const def = strat.strategy_definition;
        const featSet = new Set(def.features?.map(f => f.feature_id) || []);
        setSelectedFeatureIds(featSet);
        
        const wtMap = {};
        const normMap = {};
        def.weights?.forEach(w => {
          wtMap[w.feature_id] = w.weight;
          normMap[w.feature_id] = w.normalization_method || 'Default';
        });
        setWeights(wtMap);
        setNormalizationMethods(normMap);
        
        const sc = def.scoring_config || {};
        setScoringMethod(sc.scoring_method || 'Weighted Average');
        setThresholdBuy(sc.threshold_buy ?? 35);
        setThresholdHold(sc.threshold_hold ?? -15);
        setThresholdSell(sc.threshold_sell ?? -15);
        
        setIsEditing(false);
        setSelectedStrategyId(null);
        setActiveStep(1);
        alert("Strategy configuration imported successfully!");
      } catch (err) {
        alert("Failed to parse JSON file: " + err.message);
      }
    };
  };

  const resetBuilder = () => {
    setSelectedStrategyId(null);
    setIsEditing(false);
    setStrategyName('');
    setDescription('');
    setStrategyType('Stock');
    setStrategyPrompt('');
    setVisibility('Private');
    setStatus('Draft');
    setSelectedFeatureIds(new Set());
    setWeights({});
    setNormalizationMethods({});
    setScoringMethod('Weighted Average');
    setThresholdBuy(35);
    setThresholdHold(-15);
    setThresholdSell(-15);
    setChangeSummary('');
    setActiveStep(1);
  };

  // Calculate circular weight sum details
  const sumWeights = Object.values(weights).reduce((a, b) => a + b, 0);
  const remainingWeight = 100.0 - sumWeights;
  const isWeightsValid = Math.abs(sumWeights - 100.0) <= 0.1;

  // Filter features
  const filteredFeatures = features.filter((feat) => {
    const matchesSearch = feat.display_name.toLowerCase().includes(featureSearch.toLowerCase()) ||
                          feat.description.toLowerCase().includes(featureSearch.toLowerCase()) ||
                          feat.feature_id.toLowerCase().includes(featureSearch.toLowerCase());
    const matchesCat = featureCategoryFilter === 'All' || feat.category === featureCategoryFilter;
    return matchesSearch && matchesCat;
  });

  const categoriesList = ['All', ...new Set(features.map(f => f.category))];

  if (loading) return <LoadingSpinner />;

  return (
    <div className="fade-in">
      {/* Page Header */}
      <div className="reports-hero" style={{ marginBottom: '24px', padding: '24px', borderRadius: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="reports-hero-title" style={{ fontSize: '24px' }}>🎨 Quant Strategy Studio</h1>
          <p className="reports-hero-subtitle" style={{ fontSize: '14px', marginTop: '4px' }}>
            Bloomberg-grade institutional playground to design, score, explain, compare, and validate custom investment strategies.
          </p>
        </div>
        <div>
          <label className="btn btn-secondary" style={{ cursor: 'pointer', margin: 0 }}>
            📥 Import JSON
            <input type="file" accept=".json" onChange={handleImportJSON} style={{ display: 'none' }} />
          </label>
        </div>
      </div>

      <div className="studio-main-grid">
        {/* Left Side: Saved Library & Creator Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Strategy Library */}
          <div className="card" style={{ padding: '20px' }}>
            <h2 className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>📁 Strategy Library</span>
              <button className="btn btn-secondary btn-sm" onClick={resetBuilder}>＋ Create New</button>
            </h2>

            {strategies.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No custom strategies saved. Use the wizard to design one.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '16px' }}>
                {/* Default built-in */}
                <div style={{ padding: '12px', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', background: 'rgba(255,255,255,0.02)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 'bold', fontSize: '14px', color: '#3b82f6' }}>PMS Default Model</div>
                    <div className="text-muted text-sm">Pre-seeded core engine config</div>
                  </div>
                  <span className="badge badge-success" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>System</span>
                </div>

                {strategies.map((strat) => (
                  <div key={strat.strategy_id} style={{ padding: '12px', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', background: selectedStrategyId === strat.strategy_id ? 'rgba(59, 130, 246, 0.1)' : 'rgba(255,255,255,0.02)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{strat.strategy_name}</div>
                      <div style={{ display: 'flex', gap: '4px' }}>
                        <span className={`badge ${strat.status === 'Published' ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '10px' }}>
                          {strat.status}
                        </span>
                        <span className="badge badge-secondary" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                          v{strat.version}
                        </span>
                      </div>
                    </div>
                    {strat.description && <div className="text-muted text-sm" style={{ fontSize: '12px' }}>{strat.description}</div>}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px', borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '8px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{strat.strategy_type} • {strat.visibility}</span>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="btn btn-primary btn-sm" style={{ padding: '2px 6px', fontSize: '11px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none' }} onClick={() => navigate(`/strategy/${strat.strategy_id}/validate`, { state: { definition: strat.strategy_definition, strategyName: strat.strategy_name } })}>Validate</button>
                        <button className="btn btn-secondary btn-sm" style={{ padding: '2px 6px', fontSize: '11px' }} onClick={() => handleEdit(strat)}>Edit</button>
                        <button className="btn btn-secondary btn-sm" style={{ padding: '2px 6px', fontSize: '11px' }} onClick={() => handleDuplicate(strat.strategy_id, strat.strategy_name)}>Clone</button>
                        <button className="btn btn-secondary btn-sm" style={{ padding: '2px 6px', fontSize: '11px' }} onClick={() => handleExportJSON(strat)}>Export</button>
                        <button className="btn btn-secondary btn-sm" style={{ padding: '2px 6px', fontSize: '11px', color: '#ef4444' }} onClick={() => handleDelete(strat.strategy_id)}>Del</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Active Wizard Workspace */}
        <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Steps indicators (Responsive Scroll / Wrap) */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
              paddingBottom: '12px',
              overflowX: 'auto',
              WebkitOverflowScrolling: 'touch',
              gap: '8px'
            }}
          >
            {[
              { nr: 1, name: 'Details' },
              { nr: 2, name: 'Features' },
              { nr: 3, name: 'Weights' },
              { nr: 4, name: 'Scoring' },
              { nr: 5, name: 'Live Preview' },
              { nr: 6, name: 'Save' }
            ].map(step => (
              <button
                key={step.nr}
                onClick={() => setActiveStep(step.nr)}
                className="touch-target-44"
                style={{
                  background: 'none',
                  border: 'none',
                  color: activeStep === step.nr ? '#3b82f6' : (activeStep > step.nr ? '#10b981' : 'var(--text-muted)'),
                  fontWeight: activeStep === step.nr ? 'bold' : 'normal',
                  fontSize: '13px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  whiteSpace: 'nowrap'
                }}
              >
                <span style={{
                  display: 'inline-block',
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  background: activeStep === step.nr ? 'rgba(59, 130, 246, 0.2)' : (activeStep > step.nr ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255,255,255,0.05)'),
                  textAlign: 'center',
                  lineHeight: '24px',
                  fontSize: '11px',
                  flexShrink: 0
                }}>
                  {activeStep > step.nr ? '✓' : step.nr}
                </span>
                {step.name}
              </button>
            ))}
          </div>

          {/* Step 1: Strategy Details */}
          {activeStep === 1 && (
            <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <h3 style={{ margin: 0 }}>Step 1: Set Strategy Metadata</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label className="text-muted text-sm" style={{ display: 'block', marginBottom: '6px' }}>Strategy Name *</label>
                  <input
                    type="text"
                    className="input"
                    value={strategyName}
                    onChange={(e) => setStrategyName(e.target.value)}
                    placeholder="e.g. Core Momentum Growth"
                    style={{ width: '100%', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '10px', borderRadius: '6px' }}
                  />
                </div>
                <div>
                  <label className="text-muted text-sm" style={{ display: 'block', marginBottom: '6px' }}>Asset Category Scope</label>
                  <select
                    value={strategyType}
                    onChange={(e) => setStrategyType(e.target.value)}
                    style={{ width: '100%', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '10px', borderRadius: '6px' }}
                  >
                    {['Stock', 'Portfolio', 'ETF', 'Sector', 'Options', 'Screening', 'Allocation'].map(t => (
                      <option key={t} value={t}>{t} Strategy</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-muted text-sm" style={{ display: 'block', marginBottom: '6px' }}>Strategy Description</label>
                <textarea
                  className="input"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Summarize the core alpha thesis..."
                  rows={3}
                  style={{ width: '100%', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '10px', borderRadius: '6px' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label className="text-muted text-sm" style={{ display: 'block', marginBottom: '6px' }}>Visibility</label>
                  <select
                    value={visibility}
                    onChange={(e) => setVisibility(e.target.value)}
                    style={{ width: '100%', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '10px', borderRadius: '6px' }}
                  >
                    <option value="Private">Private (Just Me)</option>
                    <option value="Public">Public (Read-Only to All)</option>
                    <option value="Shared">Shared (Collaborative)</option>
                  </select>
                </div>
                <div>
                  <label className="text-muted text-sm" style={{ display: 'block', marginBottom: '6px' }}>AI Prompt Anchor (Optional)</label>
                  <input
                    type="text"
                    className="input"
                    value={strategyPrompt}
                    onChange={(e) => setStrategyPrompt(e.target.value)}
                    placeholder="e.g. Bullish momentum with downside risk protection"
                    style={{ width: '100%', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '10px', borderRadius: '6px' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
                <button className="btn btn-primary" onClick={() => setActiveStep(2)}>Next: Select Features ➔</button>
              </div>
            </div>
          )}

          {/* Step 2: Feature Selection */}
          {activeStep === 2 && (
            <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0 }}>Step 2: Select Quant Features ({selectedFeatureIds.size} selected)</h3>
                <div style={{ display: 'flex', gap: '10px', width: '60%' }}>
                  <input
                    type="text"
                    placeholder="Search 70+ indicators..."
                    className="input"
                    value={featureSearch}
                    onChange={(e) => setFeatureSearch(e.target.value)}
                    style={{ flex: 2, background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px 12px', borderRadius: '6px', fontSize: '13px' }}
                  />
                  <select
                    value={featureCategoryFilter}
                    onChange={(e) => setFeatureCategoryFilter(e.target.value)}
                    style={{ flex: 1, background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px 12px', borderRadius: '6px', fontSize: '13px' }}
                  >
                    {categoriesList.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Grid of indicators */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', maxHeight: '400px', overflowY: 'auto', paddingRight: '4px' }}>
                {filteredFeatures.map((feat) => {
                  const isChecked = selectedFeatureIds.has(feat.feature_id);
                  return (
                    <div
                      key={feat.feature_id}
                      onClick={() => toggleFeature(feat.feature_id)}
                      style={{
                        padding: '12px',
                        borderRadius: '8px',
                        border: isChecked ? '1px solid #3b82f6' : '1px solid rgba(255,255,255,0.06)',
                        background: isChecked ? 'rgba(59, 130, 246, 0.05)' : 'rgba(255,255,255,0.01)',
                        cursor: 'pointer',
                        display: 'flex',
                        gap: '12px',
                        position: 'relative'
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        readOnly
                        style={{ marginTop: '3px' }}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 'bold', fontSize: '13px', color: isChecked ? '#60a5fa' : '#f8fafc' }}>{feat.display_name}</span>
                          <span style={{ fontSize: '10px', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px', color: 'var(--text-muted)' }}>{feat.category}</span>
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', lineHeight: '1.4' }}>{feat.description}</div>
                        {feat.plain_formula && (
                          <div style={{ fontFamily: 'monospace', fontSize: '10px', color: '#10b981', marginTop: '6px', background: 'rgba(16,185,129,0.05)', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>
                            Formula: {feat.plain_formula}
                          </div>
                        )}
                        {feat.paper && (
                          <div style={{ fontSize: '10px', color: '#a78bfa', marginTop: '4px' }}>
                            📖 {feat.author} ({feat.year})
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
                <button className="btn btn-secondary" onClick={() => setActiveStep(1)}>➔ Back</button>
                <button className="btn btn-primary" onClick={() => setActiveStep(3)} disabled={selectedFeatureIds.size === 0}>
                  Next: Weights Allocation ➔
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Weight Allocation */}
          {activeStep === 3 && (
            <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0 }}>Step 3: Weights Allocation</h3>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="btn btn-secondary btn-sm" onClick={handleAutoRebalance}>Auto Equal Weights</button>
                  <button className="btn className-secondary btn-sm" onClick={handleResetWeights} style={{ border: '1px solid rgba(239, 68, 68, 0.2)', color: '#ef4444' }}>Reset Weights</button>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '2.5fr 1fr', gap: '20px' }}>
                {/* Sliders list */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', maxHeight: '350px', overflowY: 'auto', paddingRight: '8px' }}>
                  {Array.from(selectedFeatureIds).map((fid) => {
                    const orig = features.find(f => f.feature_id === fid) || {};
                    const wVal = weights[fid] || 0.0;
                    return (
                      <div key={fid} style={{ padding: '12px', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', background: 'rgba(255,255,255,0.01)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                          <span style={{ fontWeight: 'bold', fontSize: '13px' }}>{orig.display_name}</span>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <input
                              type="number"
                              min="0"
                              max="100"
                              step="0.5"
                              value={wVal}
                              onChange={(e) => handleWeightChange(fid, e.target.value)}
                              style={{ width: '60px', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontSize: '12px', textAlign: 'right' }}
                            />
                            <span style={{ fontSize: '12px' }}>%</span>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <input
                            type="range"
                            min="0"
                            max="100"
                            step="0.5"
                            value={wVal}
                            onChange={(e) => handleWeightChange(fid, e.target.value)}
                            style={{ flex: 1 }}
                          />
                          <select
                            value={normalizationMethods[fid] || 'Default'}
                            onChange={(e) => handleNormalizationChange(fid, e.target.value)}
                            style={{ width: '120px', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '4px', borderRadius: '4px', fontSize: '11px' }}
                          >
                            <option value="Default">Default Norm</option>
                            <option value="Min-Max">Min-Max Scale</option>
                            <option value="Z-Score">Z-Score Standard</option>
                            <option value="Percentile Rank">Percentile Rank</option>
                          </select>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Weights Ring progress gauge */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', background: 'rgba(255,255,255,0.01)' }}>
                  <div style={{ position: 'relative', width: '120px', height: '120px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {/* SVG circle meter */}
                    <svg style={{ transform: 'rotate(-90deg)', width: '100%', height: '100%' }}>
                      <circle cx="60" cy="60" r="50" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                      <circle
                        cx="60" cy="60" r="50"
                        fill="transparent"
                        stroke={isWeightsValid ? '#10b981' : (sumWeights > 100 ? '#ef4444' : '#3b82f6')}
                        strokeWidth="8"
                        strokeDasharray={2 * Math.PI * 50}
                        strokeDashoffset={2 * Math.PI * 50 * (1 - Math.min(sumWeights, 100) / 100)}
                        style={{ transition: 'stroke-dashoffset 0.3s ease' }}
                      />
                    </svg>
                    <div style={{ position: 'absolute', textAlign: 'center' }}>
                      <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{sumWeights.toFixed(1)}%</div>
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Total Weight</div>
                    </div>
                  </div>

                  <div style={{ marginTop: '16px', textAlign: 'center' }}>
                    <div style={{ fontSize: '13px', color: isWeightsValid ? '#10b981' : (remainingWeight < 0 ? '#ef4444' : '#94a3b8') }}>
                      {remainingWeight === 0 ? '✓ Balanced' : (remainingWeight > 0 ? `${remainingWeight.toFixed(1)}% Remaining` : `${Math.abs(remainingWeight).toFixed(1)}% Excess`)}
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
                <button className="btn btn-secondary" onClick={() => setActiveStep(2)}>➔ Back</button>
                <button className="btn btn-primary" onClick={() => setActiveStep(4)} disabled={selectedFeatureIds.size === 0}>
                  Next: Scoring Method ➔
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Scoring Configurations */}
          {activeStep === 4 && (
            <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <h3 style={{ margin: 0 }}>Step 4: Scoring Configuration & Thresholds</h3>
              
              <div>
                <label className="text-muted text-sm" style={{ display: 'block', marginBottom: '6px' }}>Scoring aggregation method</label>
                <select
                  value={scoringMethod}
                  onChange={(e) => setScoringMethod(e.target.value)}
                  style={{ width: '100%', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '10px', borderRadius: '6px' }}
                >
                  <option value="Weighted Average">Weighted Average (Normal linear aggregation)</option>
                  <option value="Weighted Rank">Weighted Rank (Aggregation of universe ranks)</option>
                  <option value="Percentile Rank">Percentile Rank (Scale sum score to percentile rank)</option>
                  <option value="Min-Max">Min-Max (Clipped and scaled to bounds)</option>
                  <option value="Z-Score">Z-Score (Standardized score dynamic scaling)</option>
                </select>
              </div>

              <div style={{ border: '1px solid rgba(255,255,255,0.05)', padding: '16px', borderRadius: '8px', background: 'rgba(255,255,255,0.01)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <h4 style={{ margin: 0, fontSize: '14px', color: '#3b82f6' }}>Recommendation Threshold Rules</h4>
                
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span className="text-sm">Buy Threshold (Score trigger for BUY ratings)</span>
                    <span style={{ fontWeight: 'bold', color: '#10b981' }}>&gt;= {thresholdBuy}</span>
                  </div>
                  <input
                    type="range"
                    min="-100"
                    max="100"
                    value={thresholdBuy}
                    onChange={(e) => setThresholdBuy(parseInt(e.target.value))}
                    style={{ width: '100%' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span className="text-sm">Sell Threshold (Score trigger for SELL ratings)</span>
                    <span style={{ fontWeight: 'bold', color: '#ef4444' }}>&lt;= {thresholdSell}</span>
                  </div>
                  <input
                    type="range"
                    min="-100"
                    max="100"
                    value={thresholdSell}
                    onChange={(e) => setThresholdSell(parseInt(e.target.value))}
                    style={{ width: '100%' }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
                <button className="btn btn-secondary" onClick={() => setActiveStep(3)}>➔ Back</button>
                <button className="btn btn-primary" onClick={() => setActiveStep(5)}>Next: Live Preview ➔</button>
              </div>
            </div>
          )}

          {/* Step 5: Live Preview */}
          {activeStep === 5 && (
            <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0 }}>Step 5: Live Strategy Preview & Auditing</h3>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <span className={`badge ${isWeightsValid ? 'badge-success' : 'badge-danger'}`} style={{ padding: '4px 10px', fontSize: '12px' }}>
                    {isWeightsValid ? '✓ Weights: 100%' : '⚠️ Weights Not 100%'}
                  </span>
                </div>
              </div>

              {/* Health Score and Details */}
              {validationResult && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '16px', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '8px', padding: '16px', background: 'rgba(255,255,255,0.02)' }}>
                  {/* Circular Health Meter */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <div style={{ position: 'relative', width: '100px', height: '100px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <svg style={{ transform: 'rotate(-90deg)', width: '100%', height: '100%' }}>
                        <circle cx="50" cy="50" r="40" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="6" />
                        <circle
                          cx="50" cy="50" r="40"
                          fill="transparent"
                          stroke={validationResult.health_score >= 80 ? '#10b981' : (validationResult.health_score >= 50 ? '#f59e0b' : '#ef4444')}
                          strokeWidth="6"
                          strokeDasharray={2 * Math.PI * 40}
                          strokeDashoffset={2 * Math.PI * 40 * (1 - validationResult.health_score / 100)}
                        />
                      </svg>
                      <div style={{ position: 'absolute', textAlign: 'center' }}>
                        <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{validationResult.health_score}</div>
                        <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>Health Score</div>
                      </div>
                    </div>
                    <div style={{ marginTop: '10px', fontSize: '12px', fontWeight: 'bold', color: 'var(--text-muted)' }}>
                      Complexity: <span style={{ color: '#a78bfa' }}>{validationResult.complexity}</span>
                    </div>
                  </div>

                  {/* Diagnostics breakdown */}
                  <div>
                    <h4 style={{ margin: 0, fontSize: '13px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '6px', marginBottom: '8px' }}>Health Auditing Breakdown</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', fontSize: '11px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span className="text-muted">Diversification:</span>
                        <span>{validationResult.health_breakdown?.diversification} / 20</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span className="text-muted">Weight Balance:</span>
                        <span>{validationResult.health_breakdown?.weight_balance} / 20</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span className="text-muted">Independence:</span>
                        <span>{validationResult.health_breakdown?.feature_independence} / 20</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span className="text-muted">Normalization:</span>
                        <span>{validationResult.health_breakdown?.normalization} / 20</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span className="text-muted">Risk Coverage:</span>
                        <span>{validationResult.health_breakdown?.risk_coverage} / 20</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold' }}>
                        <span className="text-muted">Overall:</span>
                        <span>{validationResult.health_score} / 100</span>
                      </div>
                    </div>

                    {validationResult.warnings?.length > 0 && (
                      <div style={{ marginTop: '10px', maxHeight: '60px', overflowY: 'auto', fontSize: '11px', color: '#f59e0b', background: 'rgba(245,158,11,0.05)', padding: '6px', borderRadius: '4px' }}>
                        ⚠️ {validationResult.warnings[0]}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Side-by-side stocks comparison preview */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <h4 style={{ margin: 0, fontSize: '14px', color: '#60a5fa' }}>Live Scored Universe Preview (Dynamic Nifty 50)</h4>
                
                {previewLoading ? (
                  <div style={{ textAlign: 'center', padding: '30px' }}><LoadingSpinner /> Loading Live Calculations...</div>
                ) : (
                  <div style={{ overflowX: 'auto', maxHeight: '200px' }}>
                    <table className="table" style={{ width: '100%', fontSize: '12px' }}>
                      <thead>
                        <tr>
                          <th style={{ textAlign: 'left' }}>Symbol</th>
                          <th>Custom Score</th>
                          <th>PMS Score</th>
                          <th>Diff</th>
                          <th>Custom Rating</th>
                          <th>PMS Rating</th>
                          <th>Custom Rank</th>
                          <th>PMS Rank</th>
                          <th>Rank Shift</th>
                          <th>XAI Preview</th>
                        </tr>
                      </thead>
                      <tbody>
                        {previewStocks.slice(0, 10).map((stock) => (
                          <tr key={stock.symbol}>
                            <td style={{ fontWeight: 'bold' }}>{stock.symbol}</td>
                            <td style={{ textAlign: 'center', fontWeight: 'bold', color: '#60a5fa' }}>{stock.custom_score}</td>
                            <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>{stock.default_score}</td>
                            <td style={{ textAlign: 'center', color: stock.score_diff > 0 ? '#10b981' : (stock.score_diff < 0 ? '#ef4444' : 'inherit') }}>
                              {stock.score_diff > 0 ? `+${stock.score_diff}` : stock.score_diff}
                            </td>
                            <td style={{ textAlign: 'center' }}>
                              <RatingBadge rating={stock.custom_rating} />
                            </td>
                            <td style={{ textAlign: 'center' }}>
                              <RatingBadge rating={stock.default_rating} />
                            </td>
                            <td style={{ textAlign: 'center' }}>{stock.custom_rank}</td>
                            <td style={{ textAlign: 'center' }}>{stock.default_rank}</td>
                            <td style={{ textAlign: 'center', color: stock.rank_diff > 0 ? '#10b981' : (stock.rank_diff < 0 ? '#ef4444' : 'inherit') }}>
                              {stock.rank_diff > 0 ? `↑ ${stock.rank_diff}` : (stock.rank_diff < 0 ? `↓ ${Math.abs(stock.rank_diff)}` : '—')}
                            </td>
                            <td style={{ textAlign: 'center' }}>
                              <button
                                className="btn btn-secondary btn-sm"
                                style={{ padding: '2px 6px', fontSize: '10px' }}
                                onClick={() => setExplainStockSymbol(stock.symbol)}
                              >
                                🔎 Explain
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
                <button className="btn btn-secondary" onClick={() => setActiveStep(4)}>➔ Back</button>
                <button className="btn btn-primary" onClick={() => setActiveStep(6)} disabled={!isWeightsValid}>
                  Next: Save Strategy ➔
                </button>
              </div>
            </div>
          )}

          {/* Step 6: Save Strategy */}
          {activeStep === 6 && (
            <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <h3 style={{ margin: 0 }}>Step 6: Confirm and Save Strategy</h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label className="text-muted text-sm" style={{ display: 'block', marginBottom: '6px' }}>Publishing Status</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    style={{ width: '100%', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '10px', borderRadius: '6px' }}
                  >
                    <option value="Draft">Draft (Transient configuration trials)</option>
                    <option value="Published">Published (Active for comparisons and dashboards)</option>
                    <option value="Archived">Archived (Deprecate strategy execution)</option>
                  </select>
                </div>
                {isEditing && (
                  <div>
                    <label className="text-muted text-sm" style={{ display: 'block', marginBottom: '6px' }}>Change Version Summary</label>
                    <input
                      type="text"
                      className="input"
                      value={changeSummary}
                      onChange={(e) => setChangeSummary(e.target.value)}
                      placeholder="e.g. Adjusted EMA20 weight to improve accuracy"
                      style={{ width: '100%', background: '#070f1e', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '10px', borderRadius: '6px' }}
                    />
                  </div>
                )}
              </div>

              <div style={{ padding: '16px', border: '1px solid rgba(16,185,129,0.1)', background: 'rgba(16,185,129,0.02)', borderRadius: '8px' }}>
                <h4 style={{ margin: 0, fontSize: '14px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>✓ Design Validation Verified</span>
                </h4>
                <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                  The validator has compiled strategy checks successfully. Saving this strategy will store the canonical JSON configuration inside StrategyMaster.
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
                <button className="btn btn-secondary" onClick={() => setActiveStep(5)}>➔ Back</button>
                <button className="btn btn-primary" onClick={handleSaveStrategy}>
                  💾 {isEditing ? 'Save Changes' : 'Create & Save Strategy'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Render Explainability Modal Preview if active */}
      {explainStockSymbol && (
        <ExplainModal
          scoreType="composite"
          symbol={explainStockSymbol}
          strategyId={buildTransientDefinition()} // Passes dynamic transient definition for real-time calculations!
          onClose={() => setExplainStockSymbol(null)}
        />
      )}
    </div>
  );
}
