package com.childai.companion.ui.chat

import android.util.Log
import com.childai.companion.BuildConfig
import com.childai.companion.config.DevSettings

object InteractionTraceLogger {
    private const val TAG = "ChildInteractionTrace"
    private const val MAX_FIELD_LENGTH = 1_500

    private var sequence = 0L

    fun log(
        event: String,
        vararg fields: Pair<String, Any?>,
    ) {
        if (!BuildConfig.DEBUG || !DevSettings.INTERACTION_TRACE_ENABLED) return
        val nextSequence = synchronized(this) {
            sequence += 1
            sequence
        }
        val body = fields.joinToString(separator = " ") { (key, value) ->
            "$key=${formatValue(value)}"
        }
        Log.d(
            TAG,
            "seq=$nextSequence at_ms=${System.currentTimeMillis()} event=${sanitize(event)} $body".trim(),
        )
    }

    private fun formatValue(value: Any?): String {
        return "\"${sanitize(value)}\""
    }

    private fun sanitize(value: Any?): String {
        val raw = when (value) {
            null -> "null"
            is Iterable<*> -> value.joinToString(prefix = "[", postfix = "]") { sanitize(it) }
            is Array<*> -> value.joinToString(prefix = "[", postfix = "]") { sanitize(it) }
            else -> value.toString()
        }
        return raw
            .replace("\\", "\\\\")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
            .replace("\"", "\\\"")
            .let {
                if (it.length <= MAX_FIELD_LENGTH) {
                    it
                } else {
                    it.take(MAX_FIELD_LENGTH) + "...<truncated>"
                }
            }
    }
}
