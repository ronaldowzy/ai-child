package com.childai.companion.data.parent

import org.junit.Assert.assertTrue
import org.junit.Test

class ParentReportApiClientTest {
    @Test
    fun parentReportReadTimeoutCoversModelGeneration() {
        assertTrue(PARENT_REPORT_READ_TIMEOUT_MS >= 60_000)
    }
}
