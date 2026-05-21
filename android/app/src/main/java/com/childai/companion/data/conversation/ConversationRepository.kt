package com.childai.companion.data.conversation

import com.childai.companion.config.DevSettings
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.UUID

class ConversationRepository(
    private val apiClient: ConversationApiClient = ConversationApiClient(),
    private val streamClient: ConversationStreamClient = ConversationStreamClient(),
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

    suspend fun requestOpening(
        childId: String,
        sessionId: String,
        timezone: String = DevSettings.TIMEZONE,
    ): ConversationMessageResponse {
        return apiClient.requestOpening(
            ConversationOpeningRequest(
                childId = childId,
                sessionId = sessionId,
                clientContext = ClientContext(
                    deviceTime = nowIsoOffset(timezone),
                    timezone = timezone,
                ),
            ),
        )
    }

    suspend fun streamTextMessage(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String> = emptyList(),
        timezone: String = DevSettings.TIMEZONE,
        includeTts: Boolean = true,
        onEvent: (ConversationStreamEvent) -> Unit,
    ) {
        streamClient.streamMessage(
            request = conversationRequest(
                childId = childId,
                sessionId = sessionId,
                text = text,
                attachments = attachments,
                timezone = timezone,
            ),
            streamOptions = ConversationStreamOptions(
                includeTts = includeTts,
                clientTurnId = "android-${UUID.randomUUID()}",
            ),
            onEvent = onEvent,
        )
    }

    private fun conversationRequest(
        childId: String,
        sessionId: String,
        text: String,
        attachments: List<String>,
        timezone: String,
    ): ConversationMessageRequest {
        return ConversationMessageRequest(
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
        )
    }

    internal fun nowIsoOffset(timezone: String): String {
        val zone = runCatching { ZoneId.of(timezone) }
            .getOrElse { ZoneId.systemDefault() }
        return OffsetDateTime.now(zone).format(DateTimeFormatter.ISO_OFFSET_DATE_TIME)
    }
}
