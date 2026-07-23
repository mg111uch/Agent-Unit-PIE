# 📂 extractors
Generated: 2026-07-23 14:15:38
Files: 3

---

F062│hypothesis_extractor.py│0
---

F061│pattern_extractor.py│0
---

F060│signal_extractor.py│185
D: ●__future__,kernel,re,typing
C: SignalExtractor│[__init__,register,extract,extract_and_emit]
F: _extract_belief_shift(data,source_unit_id)→Optional[ExtractedSignal]
F: _extract_confidence_change(data,source_unit_id)→Optional[ExtractedSignal]
F: _extract_contradiction(data,source_unit_id)→Optional[ExtractedSignal]
F: _extract_observation(data,source_unit_id)→Optional[ExtractedSignal]
C: SignalExtractor│[__init__,register,extract,extract_and_emit]
   F: __init__(self)
   F: register(self,signal_type,extractor_fn)
   F: extract(self,input_data,source_unit_id,signal_type_hint)→Optional[ExtractedSignal]
   F: extract_and_emit(self,input_data,source_unit_id,signal_type_hint)→Optional[str]
---
