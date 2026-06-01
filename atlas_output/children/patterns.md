# 📂 patterns
Generated: 2026-06-01 13:39:55
Files: 5

---

F065│anomaly_detector.py│406
D: ●kernel,math,statistics,time,typing,+2
C: AnomalyResult│[to_dict]
C: AnomalyDetector│[__init__,detect_zscore_anomalies,detect_spikes,detect_dropouts,register_anomaly_patterns,analyze_signals,summarize_anomaly]
---

F069│causal_engine.py│0
---

F066│contradiction_detector.py│0
---

F068│pattern_engine.py│411
D: ●collections,kernel,statistics,time,typing,+1
C: PatternEngine│[__init__,register_pattern,create_pattern,detect_numeric_trend,detect_repeated_events,detect_shared_sources,get_pattern,get_patterns_by_type,get_patterns_by_source,get_recent_patterns,+3]
---

F067│trend_detector.py│399
D: ●kernel,math,statistics,time,typing,+2
C: TrendResult│[to_dict]
C: TrendDetector│[__init__,detect_trend,detect_and_register_pattern,_calculate_slope,_calculate_volatility,_calculate_confidence,_get_direction,_classify_trend,moving_average,detect_anomalies,+2]
---
