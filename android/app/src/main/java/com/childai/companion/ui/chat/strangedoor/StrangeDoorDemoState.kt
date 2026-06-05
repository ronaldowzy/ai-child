package com.childai.companion.ui.chat.strangedoor

enum class StrangeDoorDemoState {
    NotStarted,
    ChoosingMethod,
    PhotoPrompt,
    PhotoUploading,
    PhotoResult,
    RiddlePrompt,
    RiddleHint,
    Completed,
}

enum class StrangeDoorState(val wireName: String) {
    Closed("closed"),
    Cracked("cracked"),
    AlmostOpen("almost_open"),
    Open("open"),
}

enum class StrangeDoorDemoMethod {
    Photo,
    Riddle,
}

enum class StrangeDoorDoorAdvanceSignal {
    None,
    AdvanceOneStep,
    Open,
}

data class StrangeDoorDemoSnapshot(
    val demoState: StrangeDoorDemoState = StrangeDoorDemoState.ChoosingMethod,
    val doorState: StrangeDoorState = StrangeDoorState.Closed,
    val attemptsCount: Int = 0,
    val lastMethod: StrangeDoorDemoMethod? = null,
    val lastObjectName: String? = null,
    val lastTransformedName: String? = null,
    val lastPhotoTransform: StrangeDoorPhotoTransform? = null,
    val lastPhotoMessageId: String? = null,
    val showcaseSaveIntentRequested: Boolean = false,
    val riddleAttempts: Int = 0,
) {
    val isCompleted: Boolean
        get() = demoState == StrangeDoorDemoState.Completed || doorState == StrangeDoorState.Open
}

object StrangeDoorDoorStateReducer {
    fun nextDoorState(
        current: StrangeDoorState,
        signal: StrangeDoorDoorAdvanceSignal,
    ): StrangeDoorState {
        return when (signal) {
            StrangeDoorDoorAdvanceSignal.None -> current
            StrangeDoorDoorAdvanceSignal.Open -> StrangeDoorState.Open
            StrangeDoorDoorAdvanceSignal.AdvanceOneStep -> when (current) {
                StrangeDoorState.Closed -> StrangeDoorState.Cracked
                StrangeDoorState.Cracked -> StrangeDoorState.AlmostOpen
                StrangeDoorState.AlmostOpen -> StrangeDoorState.Open
                StrangeDoorState.Open -> StrangeDoorState.Open
            }
        }
    }

    fun applyPhotoResult(
        snapshot: StrangeDoorDemoSnapshot,
        transform: StrangeDoorPhotoTransform,
        photoMessageId: String? = null,
    ): StrangeDoorDemoSnapshot {
        val nextDoorState = nextDoorState(snapshot.doorState, transform.advanceSignal)
        return snapshot.copy(
            demoState = if (nextDoorState == StrangeDoorState.Open) {
                StrangeDoorDemoState.Completed
            } else {
                StrangeDoorDemoState.PhotoResult
            },
            doorState = nextDoorState,
            attemptsCount = snapshot.attemptsCount + 1,
            lastMethod = StrangeDoorDemoMethod.Photo,
            lastObjectName = transform.objectName,
            lastTransformedName = transform.transformedName,
            lastPhotoTransform = transform,
            lastPhotoMessageId = photoMessageId ?: snapshot.lastPhotoMessageId,
            showcaseSaveIntentRequested = false,
        )
    }

    fun applyRiddleResult(
        snapshot: StrangeDoorDemoSnapshot,
        evaluation: StrangeDoorRiddleEvaluation,
    ): StrangeDoorDemoSnapshot {
        val nextDoorState = nextDoorState(snapshot.doorState, evaluation.advanceSignal)
        return snapshot.copy(
            demoState = if (evaluation.isCorrect || nextDoorState == StrangeDoorState.Open) {
                StrangeDoorDemoState.Completed
            } else {
                StrangeDoorDemoState.RiddleHint
            },
            doorState = nextDoorState,
            attemptsCount = snapshot.attemptsCount + 1,
            lastMethod = StrangeDoorDemoMethod.Riddle,
            riddleAttempts = snapshot.riddleAttempts + 1,
        )
    }

    fun reset(): StrangeDoorDemoSnapshot = StrangeDoorDemoSnapshot()
}
