package com.childai.companion.ui.chat

import com.childai.companion.ui.parent.ParentEntryTarget
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ParentEntryDeemphasisTest {
    @Test
    fun topBarDefaultsToOneCompactAdultEntry() {
        assertEquals(listOf("大人"), parentEntryDefaultLabels())
        assertFalse(parentEntryDefaultLabels().contains(ParentEntryTarget.Report.label))
        assertFalse(parentEntryDefaultLabels().contains(ParentEntryTarget.Settings.label))
    }

    @Test
    fun normalTapOnlyShowsFamilyFriendlyHint() {
        val hint = parentEntryTapHint()

        assertEquals("这是给家长看的，请让家长长按进入。", hint)
        assertTrue(hint.contains("家长"))
        assertTrue(hint.contains("长按"))
    }

    @Test
    fun defaultHintExplainsLongPressAndPin() {
        val hint = parentEntryDefaultHint()

        assertTrue(hint.contains("长按"))
        assertTrue(hint.contains("PIN"))
    }

    @Test
    fun longPressStillOffersReportAndSettingsTargets() {
        assertEquals(
            listOf(ParentEntryTarget.Report, ParentEntryTarget.Settings),
            parentEntryLongPressTargets(),
        )
    }
}
