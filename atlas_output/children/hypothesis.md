# 📂 hypothesis
Generated: 2026-07-23 14:15:38
Files: 3

---

F039│confidence_engine.py│471
D: ●__future__,kernel,math,statistics,time,+2
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

F037│hypothesis_engine.py│361
D: ●__future__,collections,kernel,time,typing
C: HypothesisEngine│[__init__,create_hypothesis,register_hypothesis,generate_from_patterns,add_supporting_evidence,add_contradicting_evidence,validate_hypothesis,get_hypothesis,get_by_type,get_by_category,+4]
C: HypothesisEngine│[__init__,create_hypothesis,register_hypothesis,generate_from_patterns,add_supporting_evidence,add_contradicting_evidence,validate_hypothesis,get_hypothesis,get_by_type,get_by_category,+4]
   F: __init__(self)
   F: create_hypothesis(self,hypothesis_id,title,description,hypothesis_type,category,confidence,plausibility,novelty,related_patterns,related_concepts,predictions,metadata)→Hypothesis
   F: register_hypothesis(self,hypothesis)
   F: generate_from_patterns(self,patterns)→List[Hypothesis]
   F: add_supporting_evidence(self,hypothesis_id,evidence_id)
   F: add_contradicting_evidence(self,hypothesis_id,evidence_id)
   F: validate_hypothesis(self,hypothesis_id)→Any
   F: get_hypothesis(self,hypothesis_id)→Optional[Hypothesis]
   F: get_by_type(self,hypothesis_type)→List[Hypothesis]
   F: get_by_category(self,category)→List[Hypothesis]
   F: get_by_status(self,status)→List[Hypothesis]
   F: export_to_semantic_memory(self,hypothesis_id)
   F: stats(self)→Any
   F: clear(self)
---

F038│validation_engine.py│0
---
