"""
Full Pipeline Orchestrator Use Case

Orchestrate full seed + redetection + ML dataset pipeline
"""

class FullPipelineOrchestratorUseCase:
    """
    Full Pipeline Orchestrator Use Case
    
    Run complete pipeline: seed detection -> redetection -> ML dataset
    """
    
    def __init__(self, db_path: str = "data/database/stock_data.db"):
        """Initialize orchestrator"""
        # TODO: Move implementation from scripts/redetection/run_full_pipeline.py
        pass
        
    def execute(self, **kwargs):
        """Execute full pipeline"""
        # TODO: Implement
        raise NotImplementedError("Move PipelineOrchestrator class here and rename to FullPipelineOrchestratorUseCase")
