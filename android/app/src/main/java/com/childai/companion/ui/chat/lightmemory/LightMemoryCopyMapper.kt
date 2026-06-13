package com.childai.companion.ui.chat.lightmemory

import com.childai.companion.ui.chat.strangedoor.StrangeDoorMechanismType

data class LightMemoryUiModel(
    val candidateId: String,
    val source: LightMemorySource,
    val text: String,
    val lines: List<String>,
)

object LightMemoryCopyMapper {
    fun toOpeningUiModel(snapshot: LightMemorySnapshot): LightMemoryUiModel? {
        if (snapshot.recalledInCurrentLifecycle || snapshot.mutedForCurrentLifecycle) return null
        val candidate = snapshot.openingRecallCandidate
            ?: selectOpeningCandidate(snapshot.activeCandidates)
            ?: return null
        return candidate.toOpeningUiModel()
    }

    fun selectOpeningCandidate(candidates: List<LightMemoryCandidate>): LightMemoryCandidate? {
        return candidates
            .filter { it.status == LightMemoryStatus.Active }
            .minWithOrNull(
                compareBy<LightMemoryCandidate> { it.openingPriority() }
                    .thenByDescending { it.lastTouchedAtMillis },
            )
    }

    private fun LightMemoryCandidate.toOpeningUiModel(): LightMemoryUiModel? {
        val copy = when (source) {
            LightMemorySource.ShowcaseAssist,
            LightMemorySource.ShowcaseItem,
            -> {
                val name = safeDisplayName() ?: return null
                """
                我想起了小展台里的 $name
                它好像轻轻动了一下

                不过今天想聊新的也可以
                """.trimIndent()
            }

            LightMemorySource.StrangeDoorCompleted -> completedCopy()
            LightMemorySource.StrangeDoorTool -> {
                val name = safeDisplayName() ?: return null
                strangeDoorDisplayNameCopy(name)
            }

            LightMemorySource.StrangeDoorMechanism -> mechanismCopy()
        } ?: return null
        return LightMemoryUiModel(
            candidateId = id,
            source = source,
            text = copy,
            lines = copy.lines(),
        )
    }

    private fun LightMemoryCandidate.completedCopy(): String {
        val name = safeDisplayName()
        return if (name == null) {
            """
            我好像想起一扇奇怪小门
            有个小东西曾经帮过忙

            今天也可以从新的事情开始
            """.trimIndent()
        } else {
            strangeDoorDisplayNameCopy(name)
        }
    }

    private fun strangeDoorDisplayNameCopy(name: String): String {
        return """
            我好像想起 $name
            它曾经帮过一扇奇怪小门

            今天也可以从新的事情开始
        """.trimIndent()
    }

    private fun LightMemoryCandidate.mechanismCopy(): String? {
        return when (mechanismType) {
            StrangeDoorMechanismType.Round -> """
                我好像想起一个圆圆的小机关
                它轻轻咔哒了一下

                今天想玩什么都可以
            """.trimIndent()

            StrangeDoorMechanismType.Soft -> """
                我好像想起一个软软的小机关
                它轻轻挪了一点点

                今天想玩什么都可以
            """.trimIndent()

            StrangeDoorMechanismType.Shiny -> """
                我好像想起一个亮亮的小机关
                它闪了一下又安静了

                今天想玩什么都可以
            """.trimIndent()

            null -> null
        }
    }

    private fun LightMemoryCandidate.safeDisplayName(): String? {
        return LightMemorySafetyGate.safeTextOrNull(
            showcaseItemName ?: displayName ?: toolName,
            maxLength = 24,
        )
    }

    private fun LightMemoryCandidate.openingPriority(): Int {
        return when (source) {
            LightMemorySource.ShowcaseAssist -> 0
            LightMemorySource.ShowcaseItem -> 1
            LightMemorySource.StrangeDoorCompleted -> {
                if (safeDisplayName() != null) 2 else 4
            }
            LightMemorySource.StrangeDoorTool -> 3
            LightMemorySource.StrangeDoorMechanism -> 5
        }
    }
}
