class RelationEngine:
    def link(self, source_unit: str, target_unit: str, relation_type: str, confidence: float):
        """Create directed edge: user_001 → project_x (works_on, 0.9)"""
    
    def get_relations(self, unit_id: str) -> list[Relation]:
        """Return all outbound and inbound relations for a unit"""
    
    def detect_cross_unit_correlations(self, unit_ids: list[str]) -> list[Pattern]:
        """Find patterns that span multiple units"""