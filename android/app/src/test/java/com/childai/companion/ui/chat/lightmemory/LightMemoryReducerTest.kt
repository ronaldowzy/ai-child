package com.childai.companion.ui.chat.lightmemory

import com.childai.companion.data.showcase.XiaozhantaiItem
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDemoSnapshot
import com.childai.companion.ui.chat.strangedoor.StrangeDoorDoorStateReducer
import com.childai.companion.ui.chat.strangedoor.StrangeDoorMechanismType
import com.childai.companion.ui.chat.strangedoor.StrangeDoorPhotoRecognition
import com.childai.companion.ui.chat.strangedoor.StrangeDoorPhotoTransformMapper
import com.childai.companion.ui.chat.strangedoor.StrangeDoorShapeHint
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class LightMemoryReducerTest {
    @Test
    fun emptySnapshotStartsSafe() {
        val snapshot = LightMemoryReducer.empty()

        assertTrue(snapshot.candidates.isEmpty())
        assertTrue(snapshot.activeCandidates.isEmpty())
        assertNull(snapshot.recentMechanismType)
        assertNull(snapshot.recentToolName)
        assertFalse(snapshot.recalledInCurrentLifecycle)
        assertFalse(snapshot.mutedForCurrentLifecycle)
    }

    @Test
    fun safePhotoResultRecordsMechanismAndApprovedToolName() {
        val doorSnapshot = StrangeDoorDemoSnapshot(
            mechanismType = StrangeDoorMechanismType.Round,
        )
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "图片里有一个蓝色瓶盖",
                confidence = 0.92,
            ),
            mechanismType = StrangeDoorMechanismType.Round,
        )

        val snapshot = LightMemoryReducer.rememberStrangeDoorPhotoResult(
            snapshot = LightMemorySnapshot(),
            doorSnapshot = doorSnapshot,
            transform = transform,
            nowMillis = 100L,
        )

        assertEquals(StrangeDoorMechanismType.Round, snapshot.recentMechanismType)
        assertEquals("蓝盖盖转轮", snapshot.recentToolName)
        assertTrue(snapshot.activeCandidates.any { it.source == LightMemorySource.StrangeDoorMechanism })
        assertTrue(
            snapshot.activeCandidates.any {
                it.source == LightMemorySource.StrangeDoorTool &&
                    it.toolName == "蓝盖盖转轮"
            },
        )
    }

    @Test
    fun roundSoftAndShinyOnlyRecordConfirmedMechanismTypes() {
        val mechanisms = listOf(
            StrangeDoorMechanismType.Round to "图片里有一个蓝色瓶盖",
            StrangeDoorMechanismType.Soft to "图片里有一条毛巾",
            StrangeDoorMechanismType.Shiny to "图片里有一个杯盖",
        )

        mechanisms.forEachIndexed { index, (mechanismType, text) ->
            val transform = StrangeDoorPhotoTransformMapper.map(
                StrangeDoorPhotoRecognition(
                    recognizedType = "image_observation",
                    recognizedText = text,
                    confidence = 0.92,
                ),
                mechanismType = mechanismType,
            )
            val snapshot = LightMemoryReducer.rememberStrangeDoorPhotoResult(
                snapshot = LightMemorySnapshot(),
                doorSnapshot = StrangeDoorDemoSnapshot(mechanismType = mechanismType),
                transform = transform,
                nowMillis = index.toLong(),
            )

            assertEquals(mechanismType, snapshot.recentMechanismType)
            assertTrue(
                snapshot.activeCandidates.any {
                    it.source == LightMemorySource.StrangeDoorMechanism &&
                        it.mechanismType == mechanismType
                },
            )
        }
    }

    @Test
    fun completedDoorCreatesCompletedCandidate() {
        val transform = StrangeDoorPhotoTransformMapper.map(
            StrangeDoorPhotoRecognition(
                recognizedType = "image_observation",
                recognizedText = "图片里有一个蓝色瓶盖",
                confidence = 0.92,
            ),
        )
        val almostOpenSnapshot = StrangeDoorDemoSnapshot(
            doorState = com.childai.companion.ui.chat.strangedoor.StrangeDoorState.AlmostOpen,
        )
        val completedDoorSnapshot = StrangeDoorDoorStateReducer.applyPhotoResult(
            snapshot = almostOpenSnapshot,
            transform = transform,
        )

        val snapshot = LightMemoryReducer.rememberStrangeDoorPhotoResult(
            snapshot = LightMemorySnapshot(),
            doorSnapshot = completedDoorSnapshot,
            transform = transform,
            nowMillis = 100L,
        )

        assertTrue(
            snapshot.activeCandidates.any {
                it.source == LightMemorySource.StrangeDoorCompleted &&
                    it.mechanismType == StrangeDoorMechanismType.Round
            },
        )
    }

    @Test
    fun blockedPrivacyAndHomeworkDoNotBecomeActiveCandidates() {
        val blockedCases = listOf(
            "privacy_sensitive" to "图片里有学校地址",
            "homework_problem" to "图片里有一道作业题目",
            "unsafe_unknown" to "图片里有惊吓内容",
        )

        blockedCases.forEach { (type, text) ->
            val transform = StrangeDoorPhotoTransformMapper.map(
                StrangeDoorPhotoRecognition(
                    recognizedType = type,
                    recognizedText = text,
                    confidence = 0.92,
                ),
            )
            val snapshot = LightMemoryReducer.rememberStrangeDoorPhotoResult(
                snapshot = LightMemorySnapshot(),
                doorSnapshot = StrangeDoorDemoSnapshot(),
                transform = transform,
                nowMillis = 100L,
            )

            assertEquals(StrangeDoorShapeHint.Blocked, transform.shapeHint)
            assertTrue(snapshot.activeCandidates.isEmpty())
        }
    }

    @Test
    fun showcaseItemReadsOnlyAllowedSafeFields() {
        val snapshot = LightMemoryReducer.rememberShowcaseItem(
            snapshot = LightMemorySnapshot(),
            item = showcaseItem(
                id = "stand_item_1",
                name = "蓝盖盖转轮",
                foxQuote = "门上的圆锁轻轻转了一小下",
                createdAt = 123L,
            ),
            nowMillis = 200L,
        )

        val candidate = snapshot.activeCandidates.single()
        assertEquals(LightMemorySource.ShowcaseItem, candidate.source)
        assertEquals("stand_item_1", candidate.showcaseItemId)
        assertEquals("蓝盖盖转轮", candidate.showcaseItemName)
        assertEquals(123L, candidate.showcaseCreatedAtMillis)
        assertEquals("门上的圆锁轻轻转了一小下", candidate.showcaseFoxQuote)
        assertNull(candidate.toolName)
    }

    @Test
    fun riskyFoxQuoteFiltersWholeShowcaseItem() {
        val riskyQuotes = listOf(
            "这里有学校地址",
            "这是一道作业题目",
            "电话是 123",
            "身份证在这里",
            "人脸很清楚",
        )

        riskyQuotes.forEach { quote ->
            val snapshot = LightMemoryReducer.rememberShowcaseItem(
                snapshot = LightMemorySnapshot(),
                item = showcaseItem(
                    id = "stand_item_risky",
                    name = "小发现",
                    foxQuote = quote,
                ),
                nowMillis = 100L,
            )

            assertTrue(snapshot.activeCandidates.isEmpty())
        }
    }

    @Test
    fun showcaseAssistMarksAssistedDoorInCurrentLifecycle() {
        val snapshot = LightMemoryReducer.rememberShowcaseAssist(
            snapshot = LightMemorySnapshot(),
            item = showcaseItem(
                id = "stand_item_assist",
                name = "蓝盖盖转轮",
                foxQuote = "门上的圆锁轻轻转了一小下",
            ),
            doorSnapshot = StrangeDoorDemoSnapshot(
                mechanismType = StrangeDoorMechanismType.Soft,
            ),
            nowMillis = 100L,
        )

        val candidate = snapshot.activeCandidates.single { it.source == LightMemorySource.ShowcaseAssist }
        assertEquals("stand_item_assist", candidate.showcaseItemId)
        assertEquals("蓝盖盖转轮", candidate.showcaseItemName)
        assertTrue(candidate.assistedDoorInCurrentLifecycle)
        assertEquals(StrangeDoorMechanismType.Soft, snapshot.recentMechanismType)
    }

    @Test
    fun openingRecallCanBeMarkedOnlyOncePerLifecycle() {
        val snapshot = LightMemoryReducer.rememberShowcaseItem(
            snapshot = LightMemorySnapshot(),
            item = showcaseItem(id = "stand_item_1"),
            nowMillis = 100L,
        ).let {
            LightMemoryReducer.withOpeningRecallEligibility(
                snapshot = it,
                strangeDoorActive = false,
                languageGameActive = false,
            )
        }

        val recalled = LightMemoryReducer.markOpeningRecalled(snapshot)
        val recalledAgain = LightMemoryReducer.markOpeningRecalled(recalled)

        assertTrue(recalled.recalledInCurrentLifecycle)
        assertNull(recalled.openingRecallCandidateId)
        assertEquals(recalled, recalledAgain)
        assertTrue(recalled.activeCandidates.isEmpty())
    }

    @Test
    fun relatedChatEligibilityRequiresApprovedKeywordAndActiveCandidate() {
        val snapshot = LightMemoryReducer.rememberShowcaseItem(
            snapshot = LightMemorySnapshot(),
            item = showcaseItem(id = "stand_item_1"),
            nowMillis = 100L,
        )

        val unrelated = LightMemoryReducer.withRelatedChatEligibility(
            snapshot = snapshot,
            childText = "今天想随便聊聊",
            strangeDoorActive = false,
            languageGameActive = false,
        )
        val related = LightMemoryReducer.withRelatedChatEligibility(
            snapshot = snapshot,
            childText = "我放进去的小发现还在吗",
            strangeDoorActive = false,
            languageGameActive = false,
        )

        assertNull(unrelated.relatedChatCandidateId)
        assertEquals(snapshot.activeCandidates.first().id, related.relatedChatCandidateId)
    }

    @Test
    fun candidateDoesNotDeclareForbiddenRawFields() {
        val fields = LightMemoryCandidate::class.java.declaredFields.map { it.name }.toSet()

        LightMemorySafetyGate.forbiddenFieldNames.forEach { forbidden ->
            assertFalse(fields.contains(forbidden))
        }
    }

    private fun showcaseItem(
        id: String = "stand_item",
        name: String = "小发现",
        foxQuote: String = "小白狐看见了这个小发现。",
        createdAt: Long = 1_700_000_000L,
    ): XiaozhantaiItem {
        return XiaozhantaiItem(
            id = id,
            photoUri = "/tmp/test-showcase-item.jpg",
            name = name,
            foxQuote = foxQuote,
            createdAt = createdAt,
            source = "test",
            isDeleted = false,
        )
    }
}
