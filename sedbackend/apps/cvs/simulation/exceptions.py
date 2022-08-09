class ProcessNotFoundException(Exception):
    pass

class DSMFileNotFoundException(Exception):
    pass

class EntityRateOutOfOrderException(Exception):
    pass

class FormulaEvalException(Exception):
    def __init__(self, process_id) -> None:
        self.process_id = process_id