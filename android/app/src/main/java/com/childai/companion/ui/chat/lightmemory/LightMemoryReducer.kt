package com.childai.companion.ui.chat.lightmemory

import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.data.showcase.xiaozhantaiNormalizeFoxQuote
import com.childai.companion.data.showcase.xiaozhantaiNormalizeName
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoSnapshot
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDoorAdvanceSignal
import com.childai.companion.ui.chat.strangedoor.StrangeDoorMechanismType
import com.childai.companion.ui.chat.strangedoor.StrangeDoorPhotoTransform
import com.childai.companion.ui.chat.strangedoor.StrangeDoorShapeHint

object LightMemoryReducer {
    fun empty(): LightMemorySnapshot = LightMemorySnapshot()

    fun rememberStrangeDoorPhotoResult(
        snapshot: LightMemorySnapshot,
        doorSnapshot: StrangeDoorDemoSnapshot,
        transform: StrangeDoorPhotoTransform,
        nowMillis: Long,
    ): LightMemorySnapshot {
        if (!transform.isSafeLightMemoryPhotoResult()) {
            return withOpeningRecallEligibility(
                snapshot = snapshot,
                strangeDoorActive = true,
                languageGameActive = false,
            )
        }
        val mechanismType = doorSnapshot.mechanismType
        val toolName = LightMemorySafetyGate.safeTextOrNull(transform.transformedName)
            ?: return snapshot
        val mechanismCandidate = LightMemoryCandidate(
            id = memoryId("strange_door_mechanism", mechanismType.name),
            source = LightMemorySource.StrangeDoorMechanism,
            safeLabel = mechanismType.safeLabel(),
            mechanismType = mechanismType,
            lastTouchedAtMillis = nowMillis,
        )
        val toolCandidate = LightMemoryCandidate(
            id = memoryId("strange_door_tool", mechanismType.name, toolName),
            source = LightMemorySource.StrangeDoorTool,
            safeLabel = "strange_door_tool",
            displayName = toolName,
            mechanismType = mechanismType,
            toolName = toolName,
            lastTouchedAtMillis = nowMillis,
        )
        val completedCandidate = if (doorSnapshot.isCompleted) {
            LightMemoryCandidate(
                id = memoryId("strange_door_completed", mechanismType.name, toolName),
                source = LightMemorySource.StrangeDoorCompleted,
                safeLabel = "strange_door_completed",
                displayName = toolName,
                mechanismType = mechanismType,
                toolName = toolName,
                lastTouchedAtMillis = nowMillis,
            )
        } else {
            null
        }
        return snapshot
            .rememberCandidates(
                listOfNotNull(mechanismCandidate, toolCandidate, completedCandidate),
            )
            .copy(
                recentMechanismType = mechanismType,
                recentToolName = toolName,
            )
            .let {
                withOpeningRecallEligibility(
                    snapshot = it,
                    strangeDoorActive = true,
                    languageGameActive = false,
                )
            }
    }

    fun rememberStrangeDoorCompleted(
        snapshot: LightMemorySnapshot,
        doorSnapshot: StrangeDoorDemoSnapshot,
        nowMillis: Long,
    ): LightMemorySnapshot {
        if (!doorSnapshot.isCompleted) return snapshot
        val mechanismType = doorSnapshot.mechanismType
        val safeToolName = LightMemorySafetyGate.safeTextOrNull(
            doorSnapshot.lastPhotoTransform?.transformedName
                ?: doorSnapshot.lastShowcaseAssistResult?.itemName,
        )
        val completedCandidate = LightMemoryCandidate(
            id = memoryId("strange_door_completed", mechanismType.name, safeToolName.orEmpty()),
            source = LightMemorySource.StrangeDoorCompleted,
            safeLabel = "strange_door_completed",
            displayName = safeToolName,
            mechanismType = mechanismType,
            toolName = safeToolName,
            lastTouchedAtMillis = nowMillis,
        )
        return snapshot
            .rememberCandidates(listOf(completedCandidate))
            .copy(
                recentMechanismType = mechanismType,
                recentToolName = safeToolName ?: snapshot.recentToolName,
            )
            .let {
                withOpeningRecallEligibility(
                    snapshot = it,
                    strangeDoorActive = true,
                    languageGameActive = false,
                )
            }
    }

    fun rememberShowcaseItem(
        snapshot: LightMemorySnapshot,
        item: XiaozhantaiItem,
        nowMillis: Long,
    ): LightMemorySnapshot {
        val candidate = item.toLightMemoryCandidate(
            source = LightMemorySource.ShowcaseItem,
            assistedDoor = false,
            nowMillis = nowMillis,
        ) ?: return snapshot
        return snapshot
            .rememberCandidates(listOf(candidate))
            .let {
                withOpeningRecallEligibility(
                    snapshot = it,
                    strangeDoorActive = false,
                    languageGameActive = false,
                )
            }
    }

    fun rememberShowcaseAssist(
        snapshot: LightMemorySnapshot,
        item: XiaozhantaiItem,
        doorSnapshot: StrangeDoorDemoSnapshot,
        nowMillis: Long,
    ): LightMemorySnapshot {
        val assistCandidate = item.toLightMemoryCandidate(
            source = LightMemorySource.ShowcaseAssist,
            assistedDoor = true,
            nowMillis = nowMillis,
            mechanismType = doorSnapshot.mechanismType,
        ) ?: return snapshot
        val safeName = assistCandidate.showcaseItemName
        val completedCandidate = if (doorSnapshot.isCompleted) {
            LightMemoryCandidate(
                id = memoryId("strange_door_completed", doorSnapshot.mechanismType.name, safeName.orEmpty()),
                source = LightMemorySource.StrangeDoorCompleted,
                safeLabel = "strange_door_completed",
                displayName = safeName,
                mechanismType = doorSnapshot.mechanismType,
                toolName = safeName,
                showcaseItemId = assistCandidate.showcaseItemId,
                showcaseItemName = safeName,
                showcaseCreatedAtMillis = assistCandidate.showcaseCreatedAtMillis,
                showcaseFoxQuote = assistCandidate.showcaseFoxQuote,
                assistedDoorInCurrentLifecycle = true,
                lastTouchedAtMillis = nowMillis,
            )
        } else {
            null
        }
        return snapshot
            .rememberCandidates(listOfNotNull(assistCandidate, completedCandidate))
            .copy(
                recentMechanismType = doorSnapshot.mechanismType,
                recentToolName = safeName ?: snapshot.recentToolName,
            )
            .let {
                withOpeningRecallEligibility(
                    snapshot = it,
                    strangeDoorActive = true,
                    languageGameActive = false,
                )
            }
    }

    fun withOpeningRecallEligibility(
        snapshot: LightMemorySnapshot,
        strangeDoorActive: Boolean,
        languageGameActive: Boolean,
    ): LightMemorySnapshot {
        if (
            strangeDoorActive ||
            languageGameActive ||
            snapshot.recalledInCurrentLifecycle ||
            snapshot.mutedForCurrentLifecycle
        ) {
            return snapshot.copy(openingRecallCandidateId = null)
        }
        return snapshot.copy(
            openingRecallCandidateId = LightMemoryCopyMapper
                .selectOpeningCandidate(snapshot.activeCandidates)
                ?.id,
        )
    }

    fun markOpeningRecalled(snapshot: LightMemorySnapshot): LightMemorySnapshot {
        val candidateId = snapshot.openingRecallCandidateId
            ?: snapshot.activeCandidates.maxByOrNull { it.lastTouchedAtMillis }?.id
            ?: return snapshot
        return snapshot.copy(
            candidates = snapshot.candidates.map { candidate ->
                if (candidate.id == candidateId) {
                    candidate.copy(status = LightMemoryStatus.RecalledInCurrentLifecycle)
                } else {
                    candidate
                }
            },
            recalledInCurrentLifecycle = true,
            lastRecalledCandidateId = candidateId,
            openingRecallCandidateId = null,
        )
    }

    fun muteForCurrentLifecycle(snapshot: LightMemorySnapshot): LightMemorySnapshot {
        return snapshot.copy(
            candidates = snapshot.candidates.map { candidate ->
                if (candidate.status == LightMemoryStatus.Active) {
                    candidate.copy(status = LightMemoryStatus.MutedForCurrentLifecycle)
                } else {
                    candidate
                }
            },
            skipCountInCurrentLifecycle = snapshot.skipCountInCurrentLifecycle + 1,
            mutedForCurrentLifecycle = true,
            openingRecallCandidateId = null,
            relatedChatCandidateId = null,
        )
    }

    fun withRelatedChatEligibility(
        snapshot: LightMemorySnapshot,
        childText: String,
        strangeDoorActive: Boolean,
        languageGameActive: Boolean,
    ): LightMemorySnapshot {
        if (
            strangeDoorActive ||
            languageGameActive ||
            !LightMemorySafetyGate.isRelatedChatText(childText)
        ) {
            return snapshot.copy(relatedChatCandidateId = null)
        }
        return snapshot.copy(
            relatedChatCandidateId = snapshot.activeCandidates
                .maxByOrNull { it.lastTouchedAtMillis }
                ?.id,
        )
    }

    private fun LightMemorySnapshot.rememberCandidates(
        nextCandidates: List<LightMemoryCandidate>,
    ): LightMemorySnapshot {
        val accepted = nextCandidates
            .mapNotNull { candidate ->
                val normalized = candidate.copy(
                    displayName = LightMemorySafetyGate.safeTextOrNull(candidate.displayName),
                    toolName = LightMemorySafetyGate.safeTextOrNull(candidate.toolName),
                    showcaseItemName = LightMemorySafetyGate.safeTextOrNull(candidate.showcaseItemName),
                    showcaseFoxQuote = LightMemorySafetyGate.safeTextOrNull(candidate.showcaseFoxQuote, maxLength = 80),
                )
                normalized.takeIf(LightMemorySafetyGate::acceptsCandidate)
            }
        if (accepted.isEmpty()) return this
        val acceptedIds = accepted.map { it.id }.toSet()
        val kept = candidates.filterNot { it.id in acceptedIds }
        return copy(candidates = (kept + accepted).sortedByDescending { it.lastTouchedAtMillis })
    }

    private fun XiaozhantaiItem.toLightMemoryCandidate(
        source: LightMemorySource,
        assistedDoor: Boolean,
        nowMillis: Long,
        mechanismType: StrangeDoorMechanismType? = null,
    ): LightMemoryCandidate? {
        val safeName = LightMemorySafetyGate.safeTextOrNull(
            xiaozhantaiNormalizeName(name),
            maxLength = 24,
        ) ?: return null
        val safeQuote = LightMemorySafetyGate.safeTextOrNull(
            xiaozhantaiNormalizeFoxQuote(foxQuote),
            maxLength = 80,
        ) ?: return null
        return LightMemoryCandidate(
            id = memoryId(source.name, id),
            source = source,
            safeLabel = if (assistedDoor) "showcase_assist" else "showcase_item",
            displayName = safeName,
            mechanismType = mechanismType,
            toolName = if (assistedDoor) safeName else null,
            showcaseItemId = id,
            showcaseItemName = safeName,
            showcaseCreatedAtMillis = createdAt,
            showcaseFoxQuote = safeQuote,
            assistedDoorInCurrentLifecycle = assistedDoor,
            lastTouchedAtMillis = nowMillis,
        )
    }

    private fun StrangeDoorPhotoTransform.isSafeLightMemoryPhotoResult(): Boolean {
        return isUsable &&
            canSaveToShowcase &&
            shapeHint != StrangeDoorShapeHint.Blocked &&
            advanceSignal != StrangeDoorDoorAdvanceSignal.None &&
            !LightMemorySafetyGate.containsSensitiveContent(transformedName) &&
            !LightMemorySafetyGate.containsSensitiveContent(objectName)
    }

    private fun StrangeDoorMechanismType.safeLabel(): String {
        return when (this) {
            StrangeDoorMechanismType.Round -> "round"
            StrangeDoorMechanismType.Soft -> "soft"
            StrangeDoorMechanismType.Shiny -> "shiny"
        }
    }

    private fun memoryId(prefix: String, vararg parts: String): String {
        val raw = parts.joinToString(separator = "_")
        val readable = raw
            .replace(Regex("[^A-Za-z0-9_]+"), "_")
            .trim('_')
            .take(24)
            .ifBlank { "empty" }
        return "${prefix}_${readable}_${Integer.toHexString(raw.hashCode())}"
    }
}
