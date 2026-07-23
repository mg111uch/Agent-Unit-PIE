# 📂 patterns
Generated: 2026-07-23 14:15:38
Files: 5

---

F070│anomaly_detector.py│386
D: ●__future__,kernel,math,statistics,time,+2
C: AnomalyResult│[to_dict]
C: AnomalyDetector│[__init__,detect_zscore_anomalies,detect_spikes,detect_dropouts,register_anomaly_patterns,analyze_signals,summarize_anomaly]
C: AnomalyResult│[to_dict]
   F: to_dict(self)→Any
C: AnomalyDetector│[__init__,detect_zscore_anomalies,detect_spikes,detect_dropouts,register_anomaly_patterns,analyze_signals,summarize_anomaly]
   F: __init__(self)
   F: detect_zscore_anomalies(self,signals,z_threshold)→List[AnomalyResult]
   F: detect_spikes(self,signals,spike_ratio)→List[AnomalyResult]
   F: detect_dropouts(self,signals,dropout_ratio)→List[AnomalyResult]
   F: register_anomaly_patterns(self,anomalies)→List[PatternSchema]
   F: analyze_signals(self,signals)→Any
   F: summarize_anomaly(self,anomaly)→str
---

F074│causal_engine.py│0
---

F071│contradiction_detector.py│98
D: ●__future__,dataclasses,kernel,typing
C: ContradictionResult│[to_dict]
F: detect_contradictions(believed_node_ids,relation_types,min_confidence,min_edge_weight)→List[ContradictionResult]
   ↳Called by: F071:detect_contradictions_for_beliefs
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F071:detect_contradictions_for_beliefs]
F: _resolve_to_node_id(key,info,id_field)→str
   ↳Called by: F071:detect_contradictions_for_beliefs
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F071:detect_contradictions_for_beliefs]
F: detect_contradictions_for_beliefs(beliefs,id_field,stance_field,confidence_field,agree_stances,claim_filter)→List[ContradictionResult]
   ↳Called by: F139:debate_step | Calls: F071:_resolve_to_node_id,F071:detect_contradictions
   ↳Impact: 🟢LOW (1 dependents) | Breaks: [F139:debate_step]
C: ContradictionResult│[to_dict]
   F: to_dict(self)→Any
---

F073│pattern_engine.py│383
D: ●__future__,collections,kernel,statistics,time,+1
C: PatternEngine│[__init__,register_pattern,create_pattern,detect_numeric_trend,detect_repeated_events,detect_shared_sources,get_pattern,get_patterns_by_type,get_patterns_by_source,get_recent_patterns,+3]
C: PatternEngine│[__init__,register_pattern,create_pattern,detect_numeric_trend,detect_repeated_events,detect_shared_sources,get_pattern,get_patterns_by_type,get_patterns_by_source,get_recent_patterns,+3]
   F: __init__(self)
   F: register_pattern(self,pattern,persist,add_to_memory)→PatternSchema
   F: create_pattern(self,pattern_type,title,description,source_ids,category,subtype,confidence,importance,tags,metadata)→PatternSchema
   F: detect_numeric_trend(self,signals,signal_name)→Optional[PatternSchema]
   F: detect_repeated_events(self,events,threshold)→List[PatternSchema]
   F: detect_shared_sources(self,patterns)→List[PatternSchema]
   F: get_pattern(self,pattern_id)→Optional[PatternSchema]
   F: get_patterns_by_type(self,pattern_type)→List[PatternSchema]
   F: get_patterns_by_source(self,source_id)→List[PatternSchema]
   F: get_recent_patterns(self,limit)→List[PatternSchema]
   F: remove_pattern(self,pattern_id)→bool
   F: stats(self)→Any
   F: clear(self)
---

F072│trend_detector.py│369
D: ●__future__,kernel,math,statistics,time,+2
C: TrendResult│[to_dict]
C: TrendDetector│[__init__,detect_trend,detect_and_register_pattern,_calculate_slope,_calculate_volatility,_calculate_confidence,_get_direction,_classify_trend,moving_average,detect_anomalies,+2]
C: TrendResult│[to_dict]
   F: to_dict(self)→Any
C: TrendDetector│[__init__,detect_trend,detect_and_register_pattern,_calculate_slope,_calculate_volatility,_calculate_confidence,_get_direction,_classify_trend,moving_average,detect_anomalies,+2]
   F: __init__(self)
   F: detect_trend(self,signals,trend_name)→Optional[TrendResult]
   F: detect_and_register_pattern(self,signals,trend_name)→Optional[PatternSchema]
   F: _calculate_slope(self,values)→float
   F: _calculate_volatility(self,values)→float
   F: _calculate_confidence(self,values,slope,volatility)→float
   F: _get_direction(self,slope)→str
   F: _classify_trend(self,slope,volatility)→str
   F: moving_average(self,values,window_size)→List[float]
   F: detect_anomalies(self,values,z_threshold)→Any
   F: detect_simple_cycles(self,values)→Any
   F: summarize_trend(self,result)→str
---
