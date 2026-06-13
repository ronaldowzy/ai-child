package com.childai.companion.ui.chat.lightmemory

import com.childai.companion.ui.chat.strangedoor.StrangeDoorMechanismType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class LightMemoryCopyMapperTest {
    @Test
    fun showcaseItemUsesApprovedLightCopy() {
        val model = LightMemoryCopyMapper.toOpeningUiModel(
            LightMemorySnapshot(
                candidates = listOf(
                    candidate(
                        source = LightMemorySource.ShowcaseItem,
                        name = "小石头",
                        showcaseName = "小石头",
                    ),
                ),
            ),
        )

        assertEquals(
            """
            我想起了小展台里的 小石头
            它好像轻轻动了一下

            不过今天想聊新的也可以
            """.trimIndent(),
            model?.text,
        )
    }

    @Test
    fun strangeDoorCompletedWithDisplayNameUsesApprovedCopy() {
        val model = LightMemoryCopyMapper.toOpeningUiModel(
            LightMemorySnapshot(
                candidates = listOf(
                    candidate(
                        source = LightMemorySource.StrangeDoorCompleted,
                        name = "蓝盖盖转轮",
                    ),
                ),
            ),
        )

        assertEquals(
            """
            我好像想起 蓝盖盖转轮
            它曾经帮过一扇奇怪小门

            今天也可以从新的事情开始
            """.trimIndent(),
            model?.text,
        )
    }

    @Test
    fun strangeDoorCompletedWithoutDisplayNameUsesApprovedCopy() {
        val model = LightMemoryCopyMapper.toOpeningUiModel(
            LightMemorySnapshot(
                candidates = listOf(
                    candidate(
                        source = LightMemorySource.StrangeDoorCompleted,
                        name = null,
                    ),
                ),
            ),
        )

        assertEquals(
            """
            我好像想起一扇奇怪小门
            有个小东西曾经帮过忙

            今天也可以从新的事情开始
            """.trimIndent(),
            model?.text,
        )
    }

    @Test
    fun strangeDoorToolReusesDisplayNameDoorCopy() {
        val model = LightMemoryCopyMapper.toOpeningUiModel(
            LightMemorySnapshot(
                candidates = listOf(
                    candidate(
                        source = LightMemorySource.StrangeDoorTool,
                        name = "小月亮盾牌",
                    ),
                ),
            ),
        )

        assertEquals(
            """
            我好像想起 小月亮盾牌
            它曾经帮过一扇奇怪小门

            今天也可以从新的事情开始
            """.trimIndent(),
            model?.text,
        )
    }

    @Test
    fun mechanismUsesApprovedRoundSoftAndShinyCopy() {
        val cases = listOf(
            StrangeDoorMechanismType.Round to """
                我好像想起一个圆圆的小机关
                它轻轻咔哒了一下

                今天想玩什么都可以
            """.trimIndent(),
            StrangeDoorMechanismType.Soft to """
                我好像想起一个软软的小机关
                它轻轻挪了一点点

                今天想玩什么都可以
            """.trimIndent(),
            StrangeDoorMechanismType.Shiny to """
                我好像想起一个亮亮的小机关
                它闪了一下又安静了

                今天想玩什么都可以
            """.trimIndent(),
        )

        cases.forEach { (mechanismType, expected) ->
            val model = LightMemoryCopyMapper.toOpeningUiModel(
                LightMemorySnapshot(
                    candidates = listOf(
                        candidate(
                            source = LightMemorySource.StrangeDoorMechanism,
                            name = null,
                            mechanismType = mechanismType,
                        ),
                    ),
                ),
            )

            assertEquals(expected, model?.text)
        }
    }

    @Test
    fun openingCandidatePriorityFollowsMasterOrder() {
        val candidates = listOf(
            candidate(
                source = LightMemorySource.StrangeDoorMechanism,
                name = null,
                mechanismType = StrangeDoorMechanismType.Shiny,
                lastTouchedAtMillis = 900L,
            ),
            candidate(
                source = LightMemorySource.StrangeDoorTool,
                name = "小闪光转轮",
                lastTouchedAtMillis = 800L,
            ),
            candidate(
                source = LightMemorySource.StrangeDoorCompleted,
                name = "蓝盖盖转轮",
                lastTouchedAtMillis = 700L,
            ),
            candidate(
                source = LightMemorySource.ShowcaseItem,
                name = "小石头",
                showcaseName = "小石头",
                lastTouchedAtMillis = 600L,
            ),
            candidate(
                source = LightMemorySource.ShowcaseAssist,
                name = "旧纽扣",
                showcaseName = "旧纽扣",
                lastTouchedAtMillis = 100L,
            ),
        )

        assertEquals(
            LightMemorySource.ShowcaseAssist,
            LightMemoryCopyMapper.selectOpeningCandidate(candidates)?.source,
        )
    }

    @Test
    fun samePriorityUsesLatestTouchedCandidate() {
        val oldItem = candidate(
            source = LightMemorySource.ShowcaseItem,
            name = "旧发现",
            showcaseName = "旧发现",
            lastTouchedAtMillis = 100L,
        )
        val latestItem = candidate(
            source = LightMemorySource.ShowcaseItem,
            name = "新发现",
            showcaseName = "新发现",
            lastTouchedAtMillis = 200L,
        )

        assertEquals(
            "新发现",
            LightMemoryCopyMapper.selectOpeningCandidate(listOf(oldItem, latestItem))?.displayName,
        )
    }

    @Test
    fun mutedOrRecalledSnapshotDoesNotProduceOpeningCopy() {
        val active = LightMemorySnapshot(
            candidates = listOf(candidate(source = LightMemorySource.ShowcaseItem, name = "小石头", showcaseName = "小石头")),
        )

        assertNull(
            LightMemoryCopyMapper.toOpeningUiModel(
                active.copy(recalledInCurrentLifecycle = true),
            ),
        )
        assertNull(
            LightMemoryCopyMapper.toOpeningUiModel(
                active.copy(mutedForCurrentLifecycle = true),
            ),
        )
    }

    @Test
    fun approvedCopiesDoNotContainForbiddenPhrasesOrFields() {
        val outputs = listOf(
            LightMemorySource.ShowcaseAssist to candidate(
                source = LightMemorySource.ShowcaseAssist,
                name = "小石头",
                showcaseName = "小石头",
            ),
            LightMemorySource.ShowcaseItem to candidate(
                source = LightMemorySource.ShowcaseItem,
                name = "小石头",
                showcaseName = "小石头",
            ),
            LightMemorySource.StrangeDoorCompleted to candidate(
                source = LightMemorySource.StrangeDoorCompleted,
                name = "蓝盖盖转轮",
            ),
            LightMemorySource.StrangeDoorTool to candidate(
                source = LightMemorySource.StrangeDoorTool,
                name = "小月亮盾牌",
            ),
            LightMemorySource.StrangeDoorMechanism to candidate(
                source = LightMemorySource.StrangeDoorMechanism,
                name = null,
                mechanismType = StrangeDoorMechanismType.Round,
            ),
        ).mapNotNull { (_, candidate) ->
            LightMemoryCopyMapper.toOpeningUiModel(LightMemorySnapshot(candidates = listOf(candidate)))?.text
        }

        val forbidden = listOf(
            "我一直记得你",
            "我一直在等你",
            "只有我记得",
            "这是我们的秘密",
            "通关",
            "奖励",
            "任务",
            "等级",
            "分数",
            "排名",
            "打卡",
            "rawTranscript",
            "rawPhotoBytes",
            "recognizedText",
            "childAnswer",
        )

        assertTrue(outputs.isNotEmpty())
        outputs.forEach { text ->
            forbidden.forEach { phrase ->
                assertFalse("Unexpected phrase $phrase in $text", text.contains(phrase))
            }
        }
    }

    private fun candidate(
        source: LightMemorySource,
        name: String?,
        showcaseName: String? = null,
        mechanismType: StrangeDoorMechanismType? = null,
        lastTouchedAtMillis: Long = 100L,
    ): LightMemoryCandidate {
        return LightMemoryCandidate(
            id = "${source.name}_${name.orEmpty()}_${mechanismType?.name.orEmpty()}",
            source = source,
            safeLabel = source.name,
            displayName = name,
            mechanismType = mechanismType,
            toolName = name,
            showcaseItemId = showcaseName?.let { "stand_item_$it" },
            showcaseItemName = showcaseName,
            showcaseCreatedAtMillis = showcaseName?.let { lastTouchedAtMillis },
            showcaseFoxQuote = showcaseName?.let { "门上的圆锁轻轻转了一小下" },
            assistedDoorInCurrentLifecycle = source == LightMemorySource.ShowcaseAssist,
            lastTouchedAtMillis = lastTouchedAtMillis,
        )
    }
}
