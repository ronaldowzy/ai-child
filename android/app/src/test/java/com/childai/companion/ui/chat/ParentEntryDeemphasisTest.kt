package com.childai.companion.ui.chat

import com.childai.companion.ui.parent.ParentEntryTarget
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ParentEntryDeemphasisTest {
    @Test
    fun topBarDefaultsToOneCompactParentEntry() {
        assertEquals(listOf("家长入口"), parentEntryDefaultLabels())
        assertFalse(parentEntryDefaultLabels().contains("大人"))
        assertFalse(parentEntryDefaultLabels().contains(ParentEntryTarget.Report.label))
        assertFalse(parentEntryDefaultLabels().contains(ParentEntryTarget.Settings.label))
    }

    @Test
    fun normalTapDoesNotAddExtraTopCopy() {
        val hint = parentEntryTapHint()

        assertEquals("", hint)
        assertFalse(hint.contains("大人"))
        assertFalse(hint.contains("长按"))
    }

    @Test
    fun defaultHintDoesNotLookLikePageTitle() {
        val hint = parentEntryDefaultHint()

        assertEquals("", hint)
        assertFalse(hint.contains("大人长按进入"))
        assertFalse(hint.contains("日报"))
        assertFalse(hint.contains("设置"))
    }

    @Test
    fun longPressStillOffersReportAndSettingsTargets() {
        assertEquals(
            listOf(ParentEntryTarget.Report, ParentEntryTarget.Settings),
            parentEntryLongPressTargets(),
        )
    }
}
