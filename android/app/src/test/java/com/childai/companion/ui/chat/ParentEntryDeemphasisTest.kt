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
        assertFalse(parentEntryDefaultLabels().contains("父亲日报"))
        assertFalse(parentEntryDefaultLabels().contains("父亲设置"))
    }

    @Test
    fun normalTapOnlyShowsFamilyFriendlyHint() {
        val hint = parentEntryTapHint()

        assertEquals("这是给大人看的，请让大人长按进入。", hint)
        assertTrue(hint.contains("大人"))
        assertTrue(hint.contains("长按"))
    }

    @Test
    fun longPressStillOffersReportAndSettingsTargets() {
        assertEquals(
            listOf(ParentEntryTarget.Report, ParentEntryTarget.Settings),
            parentEntryLongPressTargets(),
        )
    }
}
