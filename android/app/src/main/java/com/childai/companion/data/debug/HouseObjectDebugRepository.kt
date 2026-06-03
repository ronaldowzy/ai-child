package com.childai.companion.data.debug

open class HouseObjectDebugRepository(
    private val apiClient: HouseObjectDebugApiClient = HouseObjectDebugApiClient(),
) {
    open suspend fun create(
        visualKind: String,
        state: String,
        lightLocation: String,
    ): HouseObjectDebugCreateResponse {
        return apiClient.create(
            visualKind = visualKind,
            state = state,
            lightLocation = lightLocation,
        )
    }

    open suspend fun reset(): HouseObjectDebugResetResponse {
        return apiClient.reset()
    }
}
