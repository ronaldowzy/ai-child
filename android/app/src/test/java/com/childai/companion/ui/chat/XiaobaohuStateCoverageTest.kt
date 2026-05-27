package com.childai.companion.ui.chat

import com.childai.companion.mascot.MascotController
import com.childai.companion.mascot.MascotState
import org.junit.Assert.assertEquals
import org.junit.Test

class XiaobaohuStateCoverageTest {
    @Test
    fun childTurnPhasesMapToExpectedFoxAndMascotStates() {
        val controller = MascotController()
        val cases = listOf(
            PhaseCoverageCase(
                name = "Ready",
                phase = ChildTurnUiPhase.Ready,
                expectedMood = FoxMood.Warm,
                expectedMotion = FoxMotion.GentleIdle,
                expectedMascot = MascotState.Idle,
            ),
            PhaseCoverageCase(
                name = "Listening",
                phase = ChildTurnUiPhase.Listening,
                expectedMood = FoxMood.Listening,
                expectedMotion = FoxMotion.ListeningTail,
                expectedMascot = MascotState.Listening,
            ),
            PhaseCoverageCase(
                name = "Recognizing",
                phase = ChildTurnUiPhase.Recognizing,
                expectedMood = FoxMood.Thinking,
                expectedMotion = FoxMotion.ThinkingBlink,
                expectedMascot = MascotState.Thinking,
            ),
            PhaseCoverageCase(
                name = "Thinking",
                phase = ChildTurnUiPhase.Thinking,
                expectedMood = FoxMood.Thinking,
                expectedMotion = FoxMotion.ThinkingBlink,
                expectedMascot = MascotState.Thinking,
            ),
            PhaseCoverageCase(
                name = "SpeakingPending",
                phase = ChildTurnUiPhase.SpeakingPending,
                expectedMood = FoxMood.Warm,
                expectedMotion = FoxMotion.Speaking,
                expectedMascot = MascotState.Speaking,
            ),
            PhaseCoverageCase(
                name = "Speaking",
                phase = ChildTurnUiPhase.Speaking,
                expectedMood = FoxMood.Warm,
                expectedMotion = FoxMotion.Speaking,
                expectedMascot = MascotState.Speaking,
            ),
            PhaseCoverageCase(
                name = "ImageProcessing",
                phase = ChildTurnUiPhase.ImageProcessing,
                expectedMood = FoxMood.Thinking,
                expectedMotion = FoxMotion.ThinkingBlink,
                expectedMascot = MascotState.Thinking,
            ),
            PhaseCoverageCase(
                name = "NeedsRetry",
                phase = ChildTurnUiPhase.NeedsRetry,
                expectedMood = FoxMood.Listening,
                expectedMotion = FoxMotion.ListeningTail,
                expectedMascot = MascotState.Listening,
            ),
            PhaseCoverageCase(
                name = "PermissionNeeded",
                phase = ChildTurnUiPhase.PermissionNeeded,
                expectedMood = FoxMood.SafetyConcern,
                expectedMotion = FoxMotion.ConcernedStill,
                expectedMascot = MascotState.SafetyConcern,
            ),
            PhaseCoverageCase(
                name = "Resting",
                phase = ChildTurnUiPhase.Resting,
                expectedMood = FoxMood.Calm,
                expectedMotion = FoxMotion.CalmStill,
                expectedMascot = MascotState.Calm,
            ),
            PhaseCoverageCase(
                name = "ServiceError",
                phase = ChildTurnUiPhase.ServiceError,
                expectedMood = FoxMood.NetworkError,
                expectedMotion = FoxMotion.NetworkError,
                expectedMascot = MascotState.NetworkError,
            ),
        )

        cases.forEach { case ->
            val presentation = childInteractionPresentation(phaseHint = case.phase)

            assertEquals("${case.name} mood", case.expectedMood, presentation.agent.mood)
            assertEquals("${case.name} motion", case.expectedMotion, presentation.agent.motion)
            assertEquals(
                "${case.name} mascot",
                case.expectedMascot,
                controller.stateFor(presentation.agent),
            )
        }
    }

    @Test
    fun backendSceneAgentSignalsMapToExpectedMascotStates() {
        val controller = MascotController()
        val cases = listOf(
            SceneCoverageCase(
                name = "OpeningGreeting",
                agent = FoxAgentUiState(),
                expectedMascot = MascotState.Idle,
            ),
            SceneCoverageCase(
                name = "PrivacyBoundary",
                agent = FoxAgentUiState(
                    mood = FoxMood.PrivacyBoundary,
                    motion = FoxMotion.SteadyBoundary,
                ),
                expectedMascot = MascotState.PrivacyBoundary,
            ),
            SceneCoverageCase(
                name = "SafetyConcern",
                agent = FoxAgentUiState(
                    mood = FoxMood.SafetyConcern,
                    motion = FoxMotion.ConcernedStill,
                ),
                expectedMascot = MascotState.SafetyConcern,
            ),
            SceneCoverageCase(
                name = "HomeworkFocus",
                agent = FoxAgentUiState(
                    mood = FoxMood.HomeworkFocus,
                    motion = FoxMotion.HomeworkFocus,
                ),
                expectedMascot = MascotState.HomeworkFocus,
            ),
            SceneCoverageCase(
                name = "NetworkError",
                agent = FoxAgentUiState(
                    mood = FoxMood.NetworkError,
                    motion = FoxMotion.NetworkError,
                ),
                expectedMascot = MascotState.NetworkError,
            ),
            SceneCoverageCase(
                name = "BedtimeSleepy",
                agent = FoxAgentUiState(
                    mood = FoxMood.Sleepy,
                    motion = FoxMotion.SleepyBlink,
                ),
                expectedMascot = MascotState.Sleepy,
            ),
            SceneCoverageCase(
                name = "EncouragingHappy",
                agent = FoxAgentUiState(
                    mood = FoxMood.Encouraging,
                    motion = FoxMotion.CelebrateSmall,
                ),
                expectedMascot = MascotState.JumpingHappy,
            ),
        )

        cases.forEach { case ->
            assertEquals(
                "${case.name} mascot",
                case.expectedMascot,
                controller.stateFor(case.agent),
            )
        }
    }

    @Test
    fun controllerFallsBackWithoutManifestOrUnknownAssetState() {
        val controller = MascotController()

        assertEquals(MascotState.Idle, controller.stateFor(FoxAgentUiState()))
        assertEquals(MascotState.Idle, MascotState.fromId("missing_state"))
        assertEquals(
            MascotState.JumpingHappy,
            controller.stateAfterCompletion(
                completed = MascotState.JumpingHappy,
                baseState = MascotState.Idle,
            ),
        )
    }

    private data class PhaseCoverageCase(
        val name: String,
        val phase: ChildTurnUiPhase,
        val expectedMood: FoxMood,
        val expectedMotion: FoxMotion,
        val expectedMascot: MascotState,
    )

    private data class SceneCoverageCase(
        val name: String,
        val agent: FoxAgentUiState,
        val expectedMascot: MascotState,
    )
}
