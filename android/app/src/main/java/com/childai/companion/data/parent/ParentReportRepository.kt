package com.childai.companion.data.parent

class ParentReportRepository(
    private val apiClient: ParentReportApiClient = ParentReportApiClient(),
) {
    suspend fun getReport(childId: String, date: String): ParentReport {
        return apiClient.getReport(childId, date)
    }
}
