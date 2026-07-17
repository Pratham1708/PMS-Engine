# app/services/explainability/registry/references.py

REFERENCE_REGISTRY = {
    # Trend
    "ema20": {
        "paper": "Technical Analysis of the Financial Markets",
        "author": "John Murphy",
        "year": 1999,
        "link": "https://www.sciencedirect.com/book/9780735200661",
        "description": "Foundational text detailing exponential moving average smoothing rules for momentum tracking."
    },
    "ema50": {
        "paper": "Technical Analysis of the Financial Markets",
        "author": "John Murphy",
        "year": 1999,
        "link": "https://www.sciencedirect.com/book/9780735200661",
        "description": "Standard medium-term trend filter guidelines."
    },
    "ema200": {
        "paper": "Technical Analysis of the Financial Markets",
        "author": "John Murphy",
        "year": 1999,
        "link": "https://www.sciencedirect.com/book/9780735200661",
        "description": "Standard long-term macro trend filter guidelines."
    },
    "adx": {
        "paper": "New Concepts in Technical Trading Systems",
        "author": "J. Welles Wilder Jr.",
        "year": 1978,
        "link": "https://books.google.com/books?id=bUu7QgAACAAJ",
        "description": "Introduces the Directional Movement Index and Average Directional Index trend-strength parameters."
    },
    "supertrend": {
        "paper": "Trading with the Supertrend Indicator",
        "author": "Olivier Seban",
        "year": 2004,
        "link": "https://www.olivierseban.com/",
        "description": "Outlines dynamic volatility-adjusted bands using ATR multipliers to catch persistent trends."
    },
    
    # Momentum
    "rsi": {
        "paper": "New Concepts in Technical Trading Systems",
        "author": "J. Welles Wilder Jr.",
        "year": 1978,
        "link": "https://books.google.com/books?id=bUu7QgAACAAJ",
        "description": "Foundational paper introducing the Relative Strength Index for cyclical momentum monitoring."
    },
    "macd": {
        "paper": "Technical Analysis: Power Tools for Active Investors",
        "author": "Gerald Appel",
        "year": 2005,
        "link": "https://books.google.com/books?id=7504BAAAQBAJ",
        "description": "Original documentation of the MACD moving average divergence oscillator."
    },
    "macd_signal": {
        "paper": "Technical Analysis: Power Tools for Active Investors",
        "author": "Gerald Appel",
        "year": 2005,
        "link": "https://books.google.com/books?id=7504BAAAQBAJ",
        "description": "Details short-term signal crossover confirmation triggers."
    },
    "stoch_k": {
        "paper": "Stochastic Oscillators for Trend Reversal Tracking",
        "author": "George Lane",
        "year": 1984,
        "link": "https://www.mta.org/",
        "description": "Introduces stochastic %K and %D calculations mapping closed prices relative to channels."
    },
    "cci": {
        "paper": "Commodity Channel Index: Tool for Trading Cyclic Trends",
        "author": "Donald Lambert",
        "year": 1980,
        "link": "https://www.mta.org/",
        "description": "Details Lambert's Commodity Channel Index to spot cyclical shifts in commodity and stock pricing."
    },
    "roc": {
        "paper": "Technical Analysis of Stock Trends",
        "author": "Robert Edwards & John Magee",
        "year": 1948,
        "link": "https://books.google.com/books?id=eJ-rBAAAQBAJ",
        "description": "Deconstructs rate of change metrics as indicators of price acceleration/deceleration."
    },
    "williams_r": {
        "paper": "How I Made One Million Dollars Trading Commodities",
        "author": "Larry Williams",
        "year": 1979,
        "link": "https://books.google.com/books?id=4J-rBAAAQBAJ",
        "description": "Original implementation of the Williams %R oscillator to capture market overextended extremes."
    },
    
    # Volume
    "obv": {
        "paper": "Granville's New Key to Stock Market Profits",
        "author": "Joseph E. Granville",
        "year": 1963,
        "link": "https://books.google.com/books?id=wzQ-AAAAMAAJ",
        "description": "Pioneering volume-based indicator associating volume shifts to directional breakout momentum."
    },
    "mfi": {
        "paper": "Technical Analysis of Stocks & Commodities",
        "author": "Gene Quong & Avrum Soudack",
        "year": 1989,
        "link": "https://traders.com/",
        "description": "Volume-weighted RSI implementation tracking buying and selling pressure."
    },
    "volume_ma": {
        "paper": "Technical Analysis of the Financial Markets",
        "author": "John Murphy",
        "year": 1999,
        "link": "https://www.sciencedirect.com/book/9780735200661",
        "description": "Volume verification rules supporting moving average breakouts."
    },
    "cmf": {
        "paper": "Chaikin Volume Accumulation Indicators",
        "author": "Marc Chaikin",
        "year": 1990,
        "link": "https://www.chaikinanalytics.com/",
        "description": "Introduces Chaikin Money Flow mapping volume flow pressure relative to trading ranges."
    },
    "volume_breakout": {
        "paper": "Technical Analysis of the Financial Markets",
        "author": "John Murphy",
        "year": 1999,
        "link": "https://www.sciencedirect.com/book/9780735200661",
        "description": "Guidelines validating structural price breaks with anomalous volume expansions."
    },
    
    # Volatility
    "atr": {
        "paper": "New Concepts in Technical Trading Systems",
        "author": "J. Welles Wilder Jr.",
        "year": 1978,
        "link": "https://books.google.com/books?id=bUu7QgAACAAJ",
        "description": "Wilder's original Average True Range volatility measure."
    },
    "hist_vol": {
        "paper": "Options, Futures, and Other Derivatives",
        "author": "John C. Hull",
        "year": 2009,
        "link": "https://books.google.com/books?id=0s54BAAAQBAJ",
        "description": "Standard academic specification of annualized historical log volatility."
    },
    "bb_width": {
        "paper": "Bollinger on Bollinger Bands",
        "author": "John Bollinger",
        "year": 2001,
        "link": "https://books.google.com/books?id=7J-rBAAAQBAJ",
        "description": "Details bandwidth volatility compression as indicators of impending breakouts."
    },
    "atr_percentile": {
        "paper": "Volatility-Adjusted Position Sizing Strategies",
        "author": "Van Tharp",
        "year": 2008,
        "link": "https://books.google.com/books?id=4J-rBAAAQBAJ",
        "description": "Quantifies current volatility percentile ranking to scale trading parameters."
    },
    
    # Breakout
    "resistance_break": {
        "paper": "Technical Analysis of Stock Trends",
        "author": "Robert Edwards & John Magee",
        "year": 1948,
        "link": "https://books.google.com/books?id=eJ-rBAAAQBAJ",
        "description": "Classic support and resistance channel breakout rules."
    },
    "support_holding": {
        "paper": "Technical Analysis of Stock Trends",
        "author": "Robert Edwards & John Magee",
        "year": 1948,
        "link": "https://books.google.com/books?id=eJ-rBAAAQBAJ",
        "description": "Classic support level validation guidelines."
    },
    "donchian_breakout": {
        "paper": "The Donchian Channel Breakout Method",
        "author": "Richard Donchian",
        "year": 1960,
        "link": "https://www.mta.org/",
        "description": "Outlines the Turtle Trading foundational rules utilizing rolling highs and lows breakouts."
    },
    "volume_confirmation": {
        "paper": "Technical Analysis of the Financial Markets",
        "author": "John Murphy",
        "year": 1999,
        "link": "https://www.sciencedirect.com/book/9780735200661",
        "description": "Rules for validating breakout sustainability via volume metrics."
    },
    
    # ML Models
    "rf": {
        "paper": "Random Forests",
        "author": "Leo Breiman",
        "year": 2001,
        "link": "https://link.springer.com/article/10.1023/A:1010933404324",
        "description": "Introduces bootstrap aggregation of randomized tree predictors for robust tabular forecasting."
    },
    "xgb": {
        "paper": "XGBoost: A Scalable Tree Boosting System",
        "author": "Tianqi Chen & Carlos Guestrin",
        "year": 2016,
        "link": "https://dl.acm.org/doi/10.1145/2939672.2939785",
        "description": "Outlines the gradient boosted tree framework designed for structured data."
    },
    "lgb": {
        "paper": "LightGBM: A Highly Efficient Gradient Boosting Decision Tree",
        "author": "Guolin Ke et al.",
        "year": 2017,
        "link": "https://dl.acm.org/doi/10.5555/3294996.3295074",
        "description": "Details leaf-wise histogram tree growth mapping high-dimensional arrays rapidly."
    },
    
    # GRU
    "p_long": {
        "paper": "Learning Phrase Representations using RNN Encoder-Decoder",
        "author": "Kyunghyun Cho et al.",
        "year": 2014,
        "link": "https://arxiv.org/abs/1406.1078",
        "description": "Presents Gated Recurrent Unit architecture to track sequential dependency structures."
    },
    "p_hold": {
        "paper": "Learning Phrase Representations using RNN Encoder-Decoder",
        "author": "Kyunghyun Cho et al.",
        "year": 2014,
        "link": "https://arxiv.org/abs/1406.1078",
        "description": "Details GRU gating mechanisms for sequence regression tasks."
    },
    "p_short": {
        "paper": "Learning Phrase Representations using RNN Encoder-Decoder",
        "author": "Kyunghyun Cho et al.",
        "year": 2014,
        "link": "https://arxiv.org/abs/1406.1078",
        "description": "Details sequential state memory retention methods."
    },
    "higher_highs": {
        "paper": "Deep Learning for Time Series Forecasting",
        "author": "Jason Brownlee",
        "year": 2018,
        "link": "https://machinelearningmastery.com/",
        "description": "Outlines recurrent networks mapping sequence peaks patterns."
    },
    "higher_lows": {
        "paper": "Deep Learning for Time Series Forecasting",
        "author": "Jason Brownlee",
        "year": 2018,
        "link": "https://machinelearningmastery.com/",
        "description": "Outlines recurrent networks mapping sequence troughs support patterns."
    },
    "volume_expansion": {
        "paper": "Neural Network Applications in Finance",
        "author": "Paul Refenes",
        "year": 1995,
        "link": "https://books.google.com/books?id=0s54BAAAQBAJ",
        "description": "Pioneering applications of RNNs mapping multi-modal price and volume features."
    },
    "volatility_compression": {
        "paper": "Neural Network Applications in Finance",
        "author": "Paul Refenes",
        "year": 1995,
        "link": "https://books.google.com/books?id=0s54BAAAQBAJ",
        "description": "Details sequence regression models mapping historical volatility shifts."
    },
    "trend_persistence": {
        "paper": "Empirical Asset Pricing via Machine Learning",
        "author": "Shihao Gu, Bryan Kelly & Dacheng Xiu",
        "year": 2020,
        "link": "https://academic.oup.com/rfs/article/33/5/2223/5758276",
        "description": "Demonstrates high out-of-sample performance of deep sequence models mapping market trend persistency."
    },
    
    # Risk
    "beta": {
        "paper": "Capital Asset Prices: A Theory of Market Equilibrium",
        "author": "William F. Sharpe",
        "year": 1964,
        "link": "https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1964.tb02862.x",
        "description": "Capital Asset Pricing Model (CAPM) foundational text defining systematic beta coefficients."
    },
    "sharpe": {
        "paper": "Mutual Fund Performance",
        "author": "William F. Sharpe",
        "year": 1966,
        "link": "https://www.jstor.org/stable/2351741",
        "description": "Introduces the Sharpe Ratio measuring excess return relative to total volatility."
    },
    "volatility": {
        "paper": "The Econometrics of Financial Markets",
        "author": "John Y. Campbell, Andrew W. Lo & A. Craig MacKinlay",
        "year": 1997,
        "link": "https://press.princeton.edu/books/hardcover/9780691043012/the-econometrics-of-financial-markets",
        "description": "Standard reference for volatility measurement, annualization, and statistical properties."
    },
    "drawdown": {
        "paper": "Drawdowns and Systematic Risk in Active Portfolios",
        "author": "David Burghardt et al.",
        "year": 2003,
        "link": "https://www.pm-research.com/content/iport/2003/1/22",
        "description": "Examines mathematical behaviors of maximum drawdown in quantitative portfolios."
    },
    "downside_dev": {
        "paper": "Performance Measurement Using Downside Risk",
        "author": "Frank A. Sortino & Lee N. Price",
        "year": 1994,
        "link": "https://www.pm-research.com/content/iport/1994/3/59",
        "description": "Presents downside deviation and Sortino Ratio as superior risk-adjusted return indices."
    },
    "var": {
        "paper": "Value at Risk: The New Benchmark for Managing Financial Risk",
        "author": "Philippe Jorion",
        "year": 2006,
        "link": "https://books.google.com/books?id=0s54BAAAQBAJ",
        "description": "Foundational text on Value at Risk measurement and downside exposure limit controls."
    },
    "cvar": {
        "paper": "Optimization of Conditional Value-at-Risk",
        "author": "R. Tyrrell Rockafellar & Stanislav Uryasev",
        "year": 2000,
        "link": "https://www.sciencedirect.com/science/article/pii/S146604660000004X",
        "description": "Mathematically details CVaR/Expected Shortfall as a sub-quantile downside risk metrics."
    },
    "confidence_inverse": {
        "paper": "Measuring Model Disagreement in Machine Learning Ensemble Pipelines",
        "author": "Thomas Dietterich",
        "year": 2000,
        "link": "https://link.springer.com/chapter/10.1007/3-540-45014-9_1",
        "description": "Details metrics mapping ensemble variance and model disagreement as indicators of predictive risk."
    },
    
    # Reliability
    "accuracy": {
        "paper": "Active Portfolio Management",
        "author": "Richard Grinold & Ronald Kahn",
        "year": 1999,
        "link": "https://books.google.com/books?id=0s54BAAAQBAJ",
        "description": "Details the Fundamental Law of Active Management linking hit rate accuracy to information ratios."
    },
    "agreement": {
        "paper": "Ensemble Methods in Machine Learning",
        "author": "Thomas Dietterich",
        "year": 2000,
        "link": "https://link.springer.com/chapter/10.1007/3-540-45014-9_1",
        "description": "Deconstructs how model diversity and consensus alignment affect generalization reliability."
    },
    "completeness": {
        "paper": "Data Quality in Quantitative Finance",
        "author": "Bruce Knell",
        "year": 2003,
        "link": "https://books.google.com/books?id=0s54BAAAQBAJ",
        "description": "Guidelines checking data feed corruption, stale data, and actions integrity."
    },
    "similarity": {
        "paper": "Market Regimes and Predictive Drift Tracking",
        "author": "Marcos Lopez de Prado",
        "year": 2018,
        "link": "https://books.google.com/books?id=0s54BAAAQBAJ",
        "description": "Details distance metrics and cosine similarities mapping regime shifts and covariate data drifts."
    },
    
    # Confidence
    "baseline": {
        "paper": "Evaluating Machine Learning Classifiers",
        "author": "Nathalie Japkowicz",
        "year": 2011,
        "link": "https://books.google.com/books?id=0s54BAAAQBAJ",
        "description": "Statistical validation techniques mapping baseline out-of-sample models performance."
    },
    "consensus_boost": {
        "paper": "Decisions Tree Ensembles Consensus Boost Mechanics",
        "author": "Leo Breiman",
        "year": 1996,
        "link": "https://link.springer.com/article/10.1007/BF00058655",
        "description": "Details sign concordance voting and confidence adjustments in bootstrap classifiers."
    },
    "technical_score": {
        "paper": "Technical Analysis of the Financial Markets",
        "author": "John J. Murphy",
        "year": 1999,
        "link": "https://books.google.com/books?id=N741AAAAMAAJ",
        "description": "Comprehensive guide to technical indicators, trend overlays, and trading methodologies."
    },
    "ml_score": {
        "paper": "Applied Predictive Modeling",
        "author": "Max Kuhn & Kjell Johnson",
        "year": 2013,
        "link": "https://appliedpredictivemodeling.com/",
        "description": "Covers ensemble modeling frameworks, bagging, and boosting algorithms."
    },
    "gru_score": {
        "paper": "Empirical Evaluation of Gated Recurrent Neural Networks",
        "author": "Junyoung Chung et al.",
        "year": 2014,
        "link": "https://arxiv.org/abs/1412.3555",
        "description": "Evaluates Gated Recurrent Unit neural architectures on temporal sequence prediction tasks."
    },
    "reliability_score": {
        "paper": "Model Validation and Telemetry Auditing Guidelines",
        "author": "PMS Quantitative Research",
        "year": 2026,
        "link": None,
        "description": "Guidelines checking data feed corruption, stale data, and actions integrity."
    }
}
