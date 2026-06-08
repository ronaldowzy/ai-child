package com.childai.companion.ui.chat.strangedoor

enum class StrangeDoorDemoState {
    NotStarted,
    ChoosingMethod,
    PhotoPrompt,
    PhotoUploading,
    PhotoResult,
    RiddlePrompt,
    RiddleHint,
    ShowcaseSaved,
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

enum class StrangeDoorMechanismType {
    Round,
    Soft,
    Shiny,
}

enum class StrangeDoorDoorAdvanceSignal {
    None,
    AdvanceOneStep,
    Open,
}

data class StrangeDoorDemoSnapshot(
    val demoState: StrangeDoorDemoState = StrangeDoorDemoState.ChoosingMethod,
    val doorState: StrangeDoorState = StrangeDoorState.Closed,
    val mechanismType: StrangeDoorMechanismType = StrangeDoorMechanismType.Round,
    val attemptsCount: Int = 0,
    val lastMethod: StrangeDoorDemoMethod? = null,
    val lastObjectName: String? = null,
    val lastTransformedName: String? = null,
    val lastPhotoTransform: StrangeDoorPhotoTransform? = null,
    val lastRiddleEvaluation: StrangeDoorRiddleEvaluation? = null,
    val lastPhotoMessageId: String? = null,
    val showcaseSaveIntentRequested: Boolean = false,
    val showcaseSavedName: String? = null,
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
            lastRiddleEvaluation = null,
            lastPhotoMessageId = photoMessageId ?: snapshot.lastPhotoMessageId,
            showcaseSaveIntentRequested = false,
            showcaseSavedName = null,
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
            lastObjectName = null,
            lastTransformedName = null,
            lastPhotoTransform = null,
            lastRiddleEvaluation = evaluation,
            riddleAttempts = snapshot.riddleAttempts + 1,
            showcaseSaveIntentRequested = false,
            showcaseSavedName = null,
        )
    }

    fun reset(): StrangeDoorDemoSnapshot = StrangeDoorDemoSnapshot()

    fun replay(snapshot: StrangeDoorDemoSnapshot): StrangeDoorDemoSnapshot {
        return reset().copy(mechanismType = snapshot.mechanismType.next())
    }

    fun requestAnotherPhoto(snapshot: StrangeDoorDemoSnapshot): StrangeDoorDemoSnapshot {
        if (snapshot.doorState != StrangeDoorState.Open) {
            return snapshot.copy(
                demoState = StrangeDoorDemoState.PhotoPrompt,
                lastMethod = StrangeDoorDemoMethod.Photo,
                lastRiddleEvaluation = null,
                showcaseSaveIntentRequested = false,
                showcaseSavedName = null,
            )
        }
        return reset().copy(
            demoState = StrangeDoorDemoState.PhotoPrompt,
            mechanismType = snapshot.mechanismType,
            lastMethod = StrangeDoorDemoMethod.Photo,
        )
    }

    private fun StrangeDoorMechanismType.next(): StrangeDoorMechanismType {
        return when (this) {
            StrangeDoorMechanismType.Round -> StrangeDoorMechanismType.Soft
            StrangeDoorMechanismType.Soft -> StrangeDoorMechanismType.Shiny
            StrangeDoorMechanismType.Shiny -> StrangeDoorMechanismType.Round
        }
    }
}
