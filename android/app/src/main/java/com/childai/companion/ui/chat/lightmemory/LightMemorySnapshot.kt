package com.childai.companion.ui.chat.lightmemory

import com.childai.companion.ui.chat.strangedoor.StrangeDoorMechanismType

enum class LightMemorySource {
    StrangeDoorCompleted,
    StrangeDoorMechanism,
    StrangeDoorTool,
    ShowcaseItem,
    ShowcaseAssist,
}

enum class LightMemoryStatus {
    Active,
    RecalledInCurrentLifecycle,
    MutedForCurrentLifecycle,
    Blocked,
}

data class LightMemoryCandidate(
    val id: String,
    val source: LightMemorySource,
    val status: LightMemoryStatus = LightMemoryStatus.Active,
    val safeLabel: String,
    val displayName: String? = null,
    val mechanismType: StrangeDoorMechanismType? = null,
    val toolName: String? = null,
    val showcaseItemId: String? = null,
    val showcaseItemName: String? = null,
    val showcaseCreatedAtMillis: Long? = null,
    val showcaseFoxQuote: String? = null,
    val assistedDoorInCurrentLifecycle: Boolean = false,
    val lastTouchedAtMillis: Long,
)

data class LightMemorySnapshot(
    val candidates: List<LightMemoryCandidate> = emptyList(),
    val recentMechanismType: StrangeDoorMechanismType? = null,
    val recentToolName: String? = null,
    val recalledInCurrentLifecycle: Boolean = false,
    val lastRecalledCandidateId: String? = null,
    val skipCountInCurrentLifecycle: Int = 0,
    val mutedForCurrentLifecycle: Boolean = false,
    val openingRecallCandidateId: String? = null,
    val relatedChatCandidateId: String? = null,
) {
    val activeCandidates: List<LightMemoryCandidate>
        get() = candidates.filter { it.status == LightMemoryStatus.Active }

    val openingRecallCandidate: LightMemoryCandidate?
        get() = openingRecallCandidateId?.let { id ->
            activeCandidates.firstOrNull { it.id == id }
        }

    val relatedChatCandidate: LightMemoryCandidate?
        get() = relatedChatCandidateId?.let { id ->
            activeCandidates.firstOrNull { it.id == id }
        }
}
