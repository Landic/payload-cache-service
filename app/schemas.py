from pydantic import BaseModel, Field, field_validator


class PayloadCreateRequest(BaseModel):
    list_1: list[str] = Field(min_length=1)
    list_2: list[str] = Field(min_length=1)

    @field_validator("list_1", "list_2")
    @classmethod
    def reject_blank_values(cls, values: list[str]) -> list[str]:
        # Keep the input semantics simple while rejecting accidental blank values.
        if any(not value.strip() for value in values):
            raise ValueError("list values must not be blank")
        return values

    def validate_same_length(self) -> None:
        if len(self.list_1) != len(self.list_2):
            raise ValueError("list_1 and list_2 must have the same length")


class CreatePayloadResponse(BaseModel):
    id: str
    message: str


class ReadPayloadResponse(BaseModel):
    output: str
