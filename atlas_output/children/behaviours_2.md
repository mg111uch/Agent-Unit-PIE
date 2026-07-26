# 📂 behaviours_2
Generated: 2026-07-26 16:20:18
Files: 3

---

F136│heal.py│56
S: behaviours/heal.py
D: ►F133 ●numpy
C: HealBehavior←BaseBehavior│[execute]
   S: Attempt to heal nearby farmers.
C: HealBehavior←BaseBehavior│[execute]
   S: Attempt to heal nearby farmers.
   F: execute(self,unit,world_state)
---

F137│move.py│42
S: behaviours/move.py
D: ►F133 ●numpy
C: MoveBehavior←BaseBehavior│[execute]
   S: Move to adjacent cell based on vision radius.
C: MoveBehavior←BaseBehavior│[execute]
   S: Move to adjacent cell based on vision radius.
   F: execute(self,unit,world_state)
---

F135│reproduce.py│67
S: behaviours/reproduce.py
D: ►F133 ●numpy
C: ReproduceBehavior←BaseBehavior│[execute]
   S: Attempt to mate with a nearby fertile partner.
C: ReproduceBehavior←BaseBehavior│[execute]
   S: Attempt to mate with a nearby fertile partner.
   F: execute(self,unit,world_state)
---
