from pydantic import BaseModel, ConfigDict, Field


class XiaobaihuTtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    emotion: str = "encourage"
    voice_version: str = Field(default="xiaobaohu_v01", alias="voiceVersion")
    force_refresh: bool = Field(default=False, alias="forceRefresh")

    model_config = ConfigDict(populate_by_name=True)


class XiaobaihuTtsResponse(BaseModel):
    audio_url: str = Field(..., alias="audioUrl")
    duration: float | None = None
    text: str
    emotion: str
    voice_version: str = Field(..., alias="voiceVersion")
    provider: str
    model: str
    cache_hit: bool = Field(..., alias="cacheHit")

    model_config = ConfigDict(populate_by_name=True)
