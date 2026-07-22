# 📂 behaviours_1
Generated: 2026-07-21 18:31:40
Files: 10

---

F282│__init__.py│48
S: behaviours/
D: ►F277,F278,F279,F280,F281,F283,F284,F285,F286,F287,F288,F289
---

F285│base_behavior.py│39
S: behaviours/base_behavior.py
D: ●typing
C: BaseBehavior│[execute]
   S: Base reusable behavior class.
C: BaseBehavior│[execute]
   S: Base reusable behavior class.
   F: execute(self,unit,world_state)→Any
      S: Execute behavior logic.
      S: Parameters
      S: ----------
      S: unit : UnitAgent
      S: The unit executing the behavior.
---

F277│consume.py│50
S: behaviours/consume.py
D: ►F285
C: ConsumeResourcesBehavior←BaseBehavior│[execute]
   S: Generic resource consumption - decay all resources.
C: ConsumeMetabolismBehavior←BaseBehavior│[execute]
   S: Consume food based on metabolism.
C: ConsumeResourcesBehavior←BaseBehavior│[execute]
   S: Generic resource consumption - decay all resources.
   F: execute(self,unit,world_state)
C: ConsumeMetabolismBehavior←BaseBehavior│[execute]
   S: Consume food based on metabolism.
   F: execute(self,unit,world_state)
---

F286│harvest.py│48
S: behaviours/harvest.py
D: ►F285
C: HarvestBehavior←BaseBehavior│[execute]
   S: Harvest crops from land patch at current position.
C: HarvestBehavior←BaseBehavior│[execute]
   S: Harvest crops from land patch at current position.
   F: execute(self,unit,world_state)
---

F279│idle.py│21
S: behaviours/idle.py
D: ►F285
C: IdleBehavior←BaseBehavior│[execute]
   S: Unit remains idle.
C: IdleBehavior←BaseBehavior│[execute]
   S: Unit remains idle.
   F: execute(self,unit,world_state)
---

F280│learn.py│31
S: behaviours/learn.py
D: ►F285
C: LearnBehavior←BaseBehavior│[execute]
   S: Learning behavior - increase intelligence.
C: LearnBehavior←BaseBehavior│[execute]
   S: Learning behavior - increase intelligence.
   F: execute(self,unit,world_state)
---

F281│produce.py│62
S: behaviours/produce.py
D: ►F285 ●numpy
C: ProduceBehavior←BaseBehavior│[execute]
   S: Produce tools and sell them to nearby farmers.
C: ProduceBehavior←BaseBehavior│[execute]
   S: Produce tools and sell them to nearby farmers.
   F: execute(self,unit,world_state)
---

F283│regrow.py│36
S: behaviours/regrow.py
D: ►F285
C: RegrowBehavior←BaseBehavior│[execute]
   S: Regrow crops towards base fertility.
C: RegrowBehavior←BaseBehavior│[execute]
   S: Regrow crops towards base fertility.
   F: execute(self,unit,world_state)
---

F278│survival.py│73
S: behaviours/survival.py
D: ►F285 ●numpy
C: SurvivalBehavior←BaseBehavior│[execute]
   S: Check if the unit dies based on various factors.
C: RegenerateEnergyBehavior←BaseBehavior│[execute]
   S: Energy regeneration.
C: SurvivalBehavior←BaseBehavior│[execute]
   S: Check if the unit dies based on various factors.
   F: execute(self,unit,world_state)
C: RegenerateEnergyBehavior←BaseBehavior│[execute]
   S: Energy regeneration.
   F: execute(self,unit,world_state)
---

F284│trade.py│107
S: behaviours/trade.py
D: ►F285 ●numpy
C: TradeBehavior←BaseBehavior│[execute]
   S: Generic trading behavior.
C: TradeBehaviorAg←BaseBehavior│[execute]
   S: Facilitate trade between agents.
C: TradeBehavior←BaseBehavior│[execute]
   S: Generic trading behavior.
   F: execute(self,unit,world_state)
C: TradeBehaviorAg←BaseBehavior│[execute]
   S: Facilitate trade between agents.
   F: execute(self,unit,world_state)
---
