package com.childai.companion.ui.parent

import com.childai.companion.config.DevSettings
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ParentPinGateTest {
    @Test
    fun acceptsDefaultDevPin() {
        assertTrue(ParentPinGate.isPinAccepted("0000", DevSettings.DEV_PARENT_PIN))
    }

    @Test
    fun trimsAccidentalWhitespaceAroundPin() {
        assertTrue(ParentPinGate.isPinAccepted(" 0000 ", DevSettings.DEV_PARENT_PIN))
    }

    @Test
    fun rejectsWrongOrBlankPin() {
        assertFalse(ParentPinGate.isPinAccepted("1234", DevSettings.DEV_PARENT_PIN))
        assertFalse(ParentPinGate.isPinAccepted("", DevSettings.DEV_PARENT_PIN))
        assertFalse(ParentPinGate.isPinAccepted("0000", ""))
    }
}
