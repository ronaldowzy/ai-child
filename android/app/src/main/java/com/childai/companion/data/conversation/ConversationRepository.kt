package com.childai.companion.data.conversation

import com.childai.companion.config.DevSettings
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter

class ConversationRepository(
    private val apiClient: ConversationApiClient = ConversationApiClient(),
) {
    suspend fun sendTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String> = emptyList(),
        timezone: String = DevSettings.TIMEZONE,
    ): ConversationMessageResponse {
        return apiClient.sendMessage(
            ConversationMessageRequest(
                childId = childId,
                sessionId = sessionId,
                input = ConversationInput(
                    text = text,
                    attachments = attachments,
                ),
                clientContext = ClientContext(
                    deviceTime = nowIsoOffset(timezone),
                    timezone = timezone,
                ),
            ),
        )
    }

    private fun nowIsoOffset(timezone: String): String {
        val zone = runCatching { ZoneId.of(timezone) }
            .getOrElse { ZoneId.systemDefault() }
        return OffsetDateTime.now(zone).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME)
    }
}
