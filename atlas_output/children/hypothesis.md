# 📂 hypothesis
Generated: 2026-07-21 18:31:40
Files: 3

---

F079│confidence_engine.py│471
D: ●__future__,kernel,math,time,typing,+2
C: ConfidenceResult│[to_dict]
C: ConfidenceEngine│[__init__,evaluate_signal_confidence,evaluate_event_confidence,evaluate_pattern_confidence,evaluate_hypothesis_confidence,_calculate_signal_evidence,_calculate_signal_consistency,_calculate_source_reliability,_calculate_temporal_score,_calculate_quantity_score,+4]
C: ConfidenceResult│[to_dict]
   F: to_dict(self)→Any
C: ConfidenceEngine│[__init__,evaluate_signal_confidence,evaluate_event_confidence,evaluate_pattern_confidence,evaluate_hypothesis_confidence,_calculate_signal_evidence,_calculate_signal_consistency,_calculate_source_reliability,_calculate_temporal_score,_calculate_quantity_score,+4]
   F: __init__(self)
   F: evaluate_signal_confidence(self,signals)→ConfidenceResult
   F: evaluate_event_confidence(self,events)→ConfidenceResult
   F: evaluate_pattern_confidence(self,patterns)→ConfidenceResult
   F: evaluate_hypothesis_confidence(self,hypothesis)→ConfidenceResult
   F: _calculate_signal_evidence(self,signals)→float
   F: _calculate_signal_consistency(self,signals)→float
   F: _calculate_source_reliability(self,sources)→float
   F: _calculate_temporal_score(self,timestamps)→float
   F: _calculate_quantity_score(self,quantity)→float
   F: _inverse_variance_score(self,values)→float
   F: _clamp_confidence(self,value)→float
   F: _empty_result(self)→ConfidenceResult
   F: summarize(self,result)→str
---

F077│hypothesis_engine.py│361
---

F078│validation_engine.py│0
---
