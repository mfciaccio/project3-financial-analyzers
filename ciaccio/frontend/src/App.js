import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = 'http://localhost:8000';

function App() {
  const [stocks, setStocks] = useState([]);
  const [selectedStock, setSelectedStock] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterSector, setFilterSector] = useState('All');

  // Fetch stock list on mount
  useEffect(() => {
    fetch(`${API_BASE}/stocks`)
      .then(res => res.json())
      .then(data => setStocks(data))
      .catch(err => setError('Failed to load stocks. Is the backend running?'));
  }, []);

  // Get unique sectors
  const sectors = ['All', ...new Set(stocks.map(s => s.sector))].sort();

  // Filter stocks by sector
  const filteredStocks = filterSector === 'All'
    ? stocks
    : stocks.filter(s => s.sector === filterSector);

  // Analyze selected stock
  const handleAnalyze = async () => {
    if (!selectedStock) return;

    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const res = await fetch(`${API_BASE}/analyze/${selectedStock}`);
      if (!res.ok) throw new Error('Analysis failed');
      const data = await res.json();
      setAnalysis(data);
    } catch (err) {
      setError('Failed to analyze stock. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationColor = (action) => {
    switch (action) {
      case 'BUY': return '#10b981';
      case 'SELL': return '#ef4444';
      case 'HOLD': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'positive': return '#10b981';
      case 'negative': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'LOW': return '#10b981';
      case 'MODERATE': return '#f59e0b';
      case 'HIGH': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className="App">
      <header className="header">
        <h1>Stock Analyzer</h1>
        <p>Select a stock to get news and AI-powered recommendations</p>
      </header>

      <main className="main">
        <section className="selector-section">
          <div className="selector-card">
            <h2>Select Stock</h2>

            <div className="filter-row">
              <label>Filter by Sector:</label>
              <select
                value={filterSector}
                onChange={(e) => setFilterSector(e.target.value)}
                className="sector-select"
              >
                {sectors.map(sector => (
                  <option key={sector} value={sector}>{sector}</option>
                ))}
              </select>
            </div>

            <div className="stock-select-row">
              <select
                value={selectedStock}
                onChange={(e) => setSelectedStock(e.target.value)}
                className="stock-select"
              >
                <option value="">-- Select a Stock --</option>
                {filteredStocks.map(stock => (
                  <option key={stock.symbol} value={stock.symbol}>
                    {stock.symbol} - {stock.company_name}
                  </option>
                ))}
              </select>

              <button
                onClick={handleAnalyze}
                disabled={!selectedStock || loading}
                className="analyze-btn"
              >
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>

            {error && <p className="error">{error}</p>}
          </div>
        </section>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Fetching news and generating recommendation...</p>
          </div>
        )}

        {analysis && (
          <div className="analysis-results">
            {/* Stock Header */}
            <section className="stock-header">
              <div className="stock-info">
                <h2>{analysis.symbol}</h2>
                <p className="company-name">{analysis.company_name}</p>
                <p className="sector">{analysis.sector} • {analysis.industry}</p>
              </div>
              <div className="price-info">
                <span className="current-price">${analysis.price.current.toFixed(2)}</span>
                <span className={`price-change ${analysis.price.change >= 0 ? 'positive' : 'negative'}`}>
                  {analysis.price.change >= 0 ? '+' : ''}{analysis.price.change.toFixed(2)}
                  ({analysis.price.change_percent.toFixed(2)}%)
                </span>
              </div>
            </section>

            {/* Recommendation */}
            <section className="recommendation-section">
              <div
                className="recommendation-card"
                style={{ borderColor: getRecommendationColor(analysis.recommendation.action) }}
              >
                <div className="rec-header">
                  <span
                    className="rec-action"
                    style={{ backgroundColor: getRecommendationColor(analysis.recommendation.action) }}
                  >
                    {analysis.recommendation.action}
                  </span>
                  <span className="rec-confidence">
                    {analysis.recommendation.confidence}% Confidence
                  </span>
                </div>

                <div className="rec-details">
                  <div className="rec-item">
                    <span className="label">Risk Level:</span>
                    <span
                      className="value risk-badge"
                      style={{ backgroundColor: getRiskColor(analysis.recommendation.risk_level) }}
                    >
                      {analysis.recommendation.risk_level}
                    </span>
                  </div>
                  <div className="rec-item">
                    <span className="label">Price Target:</span>
                    <span className="value">${analysis.recommendation.price_target?.toFixed(2)}</span>
                  </div>
                  <div className="rec-item">
                    <span className="label">Time Horizon:</span>
                    <span className="value">{analysis.recommendation.time_horizon}</span>
                  </div>
                </div>

                <div className="reasoning">
                  <h4>Analysis Reasoning:</h4>
                  <ul>
                    {analysis.recommendation.reasoning.map((reason, idx) => (
                      <li key={idx}>{reason}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>

            {/* Price Details */}
            <section className="price-details">
              <h3>Price Details</h3>
              <div className="price-grid">
                <div className="price-item">
                  <span className="label">Open</span>
                  <span className="value">${analysis.price.open.toFixed(2)}</span>
                </div>
                <div className="price-item">
                  <span className="label">High</span>
                  <span className="value">${analysis.price.high.toFixed(2)}</span>
                </div>
                <div className="price-item">
                  <span className="label">Low</span>
                  <span className="value">${analysis.price.low.toFixed(2)}</span>
                </div>
                <div className="price-item">
                  <span className="label">Prev Close</span>
                  <span className="value">${analysis.price.previous_close.toFixed(2)}</span>
                </div>
                <div className="price-item">
                  <span className="label">Volume</span>
                  <span className="value">{analysis.price.volume.toLocaleString()}</span>
                </div>
              </div>
            </section>

            {/* News */}
            <section className="news-section">
              <h3>Recent News</h3>
              <div className="news-list">
                {analysis.news.map((item, idx) => (
                  <div key={idx} className="news-item">
                    <div className="news-header">
                      <span
                        className="sentiment-badge"
                        style={{ backgroundColor: getSentimentColor(item.sentiment) }}
                      >
                        {item.sentiment}
                      </span>
                      <span className="news-source">{item.source}</span>
                      <span className="news-date">{item.published}</span>
                    </div>
                    <h4 className="news-title">{item.title}</h4>
                    <p className="news-summary">{item.summary}</p>
                  </div>
                ))}
              </div>
            </section>

            <p className="analysis-date">
              Analysis generated: {analysis.analysis_date}
            </p>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Stock Analyzer - For educational purposes only. Not financial advice.</p>
      </footer>
    </div>
  );
}

export default App;
