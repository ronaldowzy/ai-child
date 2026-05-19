package com.childai.companion.data.parent

class ParentPolicyRepository(
    private val apiClient: ParentPolicyApiClient = ParentPolicyApiClient(),
) {
    suspend fun getPolicy(childId: String): ParentPolicyResponse {
        return apiClient.getPolicy(childId)
    }

    suspend fun updatePolicy(
        request: ParentPolicyUpdateRequest,
    ): ParentPolicyResponse {
        return apiClient.updatePolicy(request)
    }
}
