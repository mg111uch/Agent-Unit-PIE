# 📂 behaviours_1
Generated: 2026-06-01 13:39:55
Files: 10

---

F116│__init__.py│48
S: behaviours/
D: ►F111,F112,F113,F114,F115,F117,F118,F119,F120,F121,F122,F123
---

F119│base_behavior.py│39
S: behaviours/base_behavior.py
D: ●typing
C: BaseBehavior│[execute]
   S: Base reusable behavior class.
---

F111│consume.py│50
S: behaviours/consume.py
D: ►F119
C: ConsumeResourcesBehavior←BaseBehavior│[execute]
   S: Generic resource consumption - decay all resources.
C: ConsumeMetabolismBehavior←BaseBehavior│[execute]
   S: Consume food based on metabolism.
---

F120│harvest.py│48
S: behaviours/harvest.py
D: ►F119
C: HarvestBehavior←BaseBehavior│[execute]
   S: Harvest crops from land patch at current position.
---

F113│idle.py│21
S: behaviours/idle.py
D: ►F119
C: IdleBehavior←BaseBehavior│[execute]
   S: Unit remains idle.
---

F114│learn.py│31
S: behaviours/learn.py
D: ►F119
C: LearnBehavior←BaseBehavior│[execute]
   S: Learning behavior - increase intelligence.
---

F115│produce.py│62
S: behaviours/produce.py
D: ►F119 ●numpy
C: ProduceBehavior←BaseBehavior│[execute]
   S: Produce tools and sell them to nearby farmers.
---

F117│regrow.py│36
S: behaviours/regrow.py
D: ►F119
C: RegrowBehavior←BaseBehavior│[execute]
   S: Regrow crops towards base fertility.
---

F112│survival.py│73
S: behaviours/survival.py
D: ►F119 ●numpy
C: SurvivalBehavior←BaseBehavior│[execute]
   S: Check if the unit dies based on various factors.
C: RegenerateEnergyBehavior←BaseBehavior│[execute]
   S: Energy regeneration.
---

F118│trade.py│107
S: behaviours/trade.py
D: ►F119 ●numpy
C: TradeBehavior←BaseBehavior│[execute]
   S: Generic trading behavior.
C: TradeBehaviorAg←BaseBehavior│[execute]
   S: Facilitate trade between agents.
---
