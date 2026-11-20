from pathlib import Path
from typing import Literal, Self
from functools import lru_cache

from app.core.config import get_settings

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

RuleAction = Literal["block", "flag", "off"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ClassifierPolicy(StrictModel):
    block_threshold: float = Field(ge=0, le=1)
    flag_threshold: float = Field(ge=0, le=1)
    on_failure: Literal["block", "allow"]

    @model_validator(mode="after")
    def check_threshold_order(self) -> Self:
        if self.flag_threshold > self.block_threshold:
            raise ValueError("flag_threshold must not be higher than block_threshold")
        return self


class RulesPolicy(StrictModel):
    ignore_instructions: RuleAction
    reveal_system_prompt: RuleAction
    role_override: RuleAction


class InputPolicy(StrictModel):
    max_chars: int = Field(gt=0)
    classifier: ClassifierPolicy
    rules: RulesPolicy


class Policy(StrictModel):
    version: int
    name: str
    input: InputPolicy


def load_policy(path: str | Path) -> Policy:
    with open(path, encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return Policy.model_validate(data)


@lru_cache
def get_policy() -> Policy:
    return load_policy(get_settings().policy_path)
