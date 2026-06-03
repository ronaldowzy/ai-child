package com.childai.companion.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.compose.viewModel
import com.childai.companion.data.attachment.AttachmentApiClient
import com.childai.companion.data.attachment.AttachmentRepository
import com.childai.companion.data.auth.AuthRepository
import com.childai.companion.data.conversation.ConversationApiClient
import com.childai.companion.data.conversation.ConversationRepository
import com.childai.companion.data.conversation.ConversationStreamClient
import com.childai.companion.data.debug.HouseObjectDebugApiClient
import com.childai.companion.data.debug.HouseObjectDebugRepository
import com.childai.companion.data.parent.ParentPolicyApiClient
import com.childai.companion.data.parent.ParentPolicyRepository
import com.childai.companion.data.parent.ParentReportApiClient
import com.childai.companion.data.parent.ParentReportRepository
import com.childai.companion.ui.auth.AuthScreen
import com.childai.companion.ui.auth.AuthViewModel
import com.childai.companion.ui.chat.ChildChatScreen
import com.childai.companion.ui.chat.ChatViewModel
import com.childai.companion.ui.chat.ConversationRepositoryMessageSender
import com.childai.companion.ui.parent.ParentReportScreen
import com.childai.companion.ui.parent.ParentReportViewModel
import com.childai.companion.ui.parent.ParentCredentialVerifier
import com.childai.companion.ui.parent.ParentPolicyViewModel
import com.childai.companion.ui.parent.ParentSettingsScreen

@Composable
fun AppNavHost(
    authRepository: AuthRepository,
) {
    val authViewModel = remember(authRepository) { AuthViewModel(authRepository) }
    val authState by authViewModel.uiState.collectAsState()
    if (!authState.isLoggedIn) {
        AuthScreen(viewModel = authViewModel)
        return
    }

    val session = authState.session
    val authTokenProvider = remember(authRepository) {
        { authRepository.authToken() }
    }
    val conversationRepository = remember(session.childId) {
        ConversationRepository(
            apiClient = ConversationApiClient(authTokenProvider = authTokenProvider),
            streamClient = ConversationStreamClient(authTokenProvider = authTokenProvider),
        )
    }
    val attachmentRepository = remember(session.childId) {
        AttachmentRepository(
            AttachmentApiClient(authTokenProvider = authTokenProvider),
        )
    }
    val parentPolicyRepository = remember(session.childId) {
        ParentPolicyRepository(
            ParentPolicyApiClient(authTokenProvider = authTokenProvider),
        )
    }
    val parentReportRepository = remember(session.childId) {
        ParentReportRepository(
            ParentReportApiClient(authTokenProvider = authTokenProvider),
        )
    }
    val houseObjectDebugRepository = remember(session.childId) {
        HouseObjectDebugRepository(
            HouseObjectDebugApiClient(authTokenProvider = authTokenProvider),
        )
    }
    val parentCredentialVerifier = remember(authRepository, session.username) {
        ParentCredentialVerifier(authRepository)
    }
    var destination by rememberSaveable { mutableStateOf(AppDestination.Chat) }

    when (destination) {
        AppDestination.Chat -> {
            val chatViewModel: ChatViewModel = viewModel(
                key = "chat-${session.childId}",
                factory = simpleViewModelFactory {
                    ChatViewModel(
                    conversationSender = ConversationRepositoryMessageSender(
                        repository = conversationRepository,
                    ),
                    attachmentRepository = attachmentRepository,
                    childId = session.childId,
                )
                },
            )
            ChildChatScreen(
                onOpenParentSettings = { destination = AppDestination.ParentSettings },
                onOpenParentReport = { destination = AppDestination.ParentReport },
                viewModel = chatViewModel,
                requireParentCredential = true,
                verifyParentCredential = parentCredentialVerifier::verify,
                houseObjectDebugRepository = houseObjectDebugRepository,
            )
        }
        AppDestination.ParentSettings -> {
            val parentPolicyViewModel = remember(session.childId) {
                ParentPolicyViewModel(
                    repository = parentPolicyRepository,
                    childId = session.childId,
                )
            }
            ParentSettingsScreen(
                onBack = { destination = AppDestination.Chat },
                viewModel = parentPolicyViewModel,
                onLogout = authViewModel::logout,
            )
        }
        AppDestination.ParentReport -> {
            val parentReportViewModel = remember(session.childId) {
                ParentReportViewModel(
                    repository = parentReportRepository,
                    childId = session.childId,
                )
            }
            ParentReportScreen(
                onBack = { destination = AppDestination.Chat },
                viewModel = parentReportViewModel,
            )
        }
    }
}

private enum class AppDestination {
    Chat,
    ParentSettings,
    ParentReport,
}

private inline fun <reified T : ViewModel> simpleViewModelFactory(
    crossinline create: () -> T,
): ViewModelProvider.Factory {
    return object : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <VM : ViewModel> create(modelClass: Class<VM>): VM {
            require(modelClass.isAssignableFrom(T::class.java)) {
                "Unsupported ViewModel class: ${modelClass.name}"
            }
            return create() as VM
        }
    }
}
