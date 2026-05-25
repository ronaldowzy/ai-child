package com.childai.companion.ui.parent

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ParentCredentialGateTest {
    @Test
    fun acceptsInjectedCredential() {
        assertTrue(ParentCredentialGate.isLocalCredentialAccepted("safe-password", "safe-password"))
    }

    @Test
    fun trimsAccidentalWhitespaceAroundCredential() {
        assertTrue(ParentCredentialGate.isLocalCredentialAccepted(" safe-password ", "safe-password"))
    }

    @Test
    fun rejectsWrongOrBlankCredential() {
        assertFalse(ParentCredentialGate.isLocalCredentialAccepted("wrong-password", "safe-password"))
        assertFalse(ParentCredentialGate.isLocalCredentialAccepted("", "safe-password"))
        assertFalse(ParentCredentialGate.isLocalCredentialAccepted("safe-password", ""))
    }
}
