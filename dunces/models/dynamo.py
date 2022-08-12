from dataclasses import dataclass, field


@dataclass
class DynamoClass:
  PK: str = field(init=False)
  SK: str = field(init=False)
  GSIPK1: str = field(init=False)
  GSISK1: str = field(init=False)
  data_type: str = field(init=False)
