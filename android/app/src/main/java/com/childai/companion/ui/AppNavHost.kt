package com.childai.companion.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
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
import com.childai.companion.data.growth.LocalGrowthEventRepository
import com.childai.companion.data.parent.ParentPolicyApiClient
import com.childai.companion.data.parent.ParentPolicyRepository
import com.childai.companion.data.parent.ParentReportApiClient
import com.childai.companion.data.parent.ParentReportRepository
import com.childai.companion.data.showcase.LocalXiaozhantaiRepository
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
import com.childai.companion.ui.showcase.XiaozhantaiDetailScreen
import com.childai.companion.ui.showcase.XiaozhantaiListScreen
import com.childai.companion.ui.showcase.XiaozhantaiPickScreen
import com.childai.companion.ui.showcase.XiaozhantaiViewModel

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
    val appContext = LocalContext.current.applicationContext
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
    val xiaozhantaiRepository = remember(session.childId) {
        LocalXiaozhantaiRepository(appContext)
    }
    val growthEventRepository = remember(session.childId) {
        LocalGrowthEventRepository(appContext)
    }
    val parentCredentialVerifier = remember(authRepository, session.username) {
        ParentCredentialVerifier(authRepository)
    }
    var destination by rememberSaveable { mutableStateOf(AppDestination.Chat) }
    var selectedXiaozhantaiItemId by rememberSaveable { mutableStateOf<String?>(null) }
    val xiaozhantaiViewModel: XiaozhantaiViewModel = viewModel(
        key = "xiaozhantai-${session.childId}",
        factory = simpleViewModelFactory {
            XiaozhantaiViewModel(
                repository = xiaozhantaiRepository,
                childId = session.childId,
            )
        },
    )
    val chatViewModel: ChatViewModel = viewModel(
        key = "chat-${session.childId}",
        factory = simpleViewModelFactory {
            ChatViewModel(
                conversationSender = ConversationRepositoryMessageSender(
                    repository = conversationRepository,
                ),
                attachmentRepository = attachmentRepository,
                xiaozhantaiRepository = xiaozhantaiRepository,
                growthEventRepository = growthEventRepository,
                childId = session.childId,
            )
        },
    )

    when (destination) {
        AppDestination.Chat -> {
            ChildChatScreen(
                onOpenParentSettings = { destination = AppDestination.ParentSettings },
                onOpenParentReport = { destination = AppDestination.ParentReport },
                onOpenXiaozhantai = { destination = AppDestination.XiaozhantaiList },
                onOpenXiaozhantaiPicker = { destination = AppDestination.XiaozhantaiPickForStrangeDoor },
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
                    growthEventRepository = growthEventRepository,
                    childId = session.childId,
                )
            }
            ParentReportScreen(
                onBack = { destination = AppDestination.Chat },
                viewModel = parentReportViewModel,
            )
        }
        AppDestination.XiaozhantaiList -> {
            XiaozhantaiListScreen(
                viewModel = xiaozhantaiViewModel,
                onBack = { destination = AppDestination.Chat },
                onOpenItem = { itemId ->
                    selectedXiaozhantaiItemId = itemId
                    xiaozhantaiViewModel.selectItem(itemId)
                    destination = AppDestination.XiaozhantaiDetail
                },
            )
        }
        AppDestination.XiaozhantaiPickForStrangeDoor -> {
            XiaozhantaiPickScreen(
                viewModel = xiaozhantaiViewModel,
                onBack = { destination = AppDestination.Chat },
                onPickItem = { itemId ->
                    val item = xiaozhantaiViewModel.uiState.value.items.firstOrNull { it.id == itemId }
                    if (item != null) {
                        chatViewModel.useXiaozhantaiItemForStrangeDoor(item)
                    }
                    destination = AppDestination.Chat
                },
            )
        }
        AppDestination.XiaozhantaiDetail -> {
            XiaozhantaiDetailScreen(
                viewModel = xiaozhantaiViewModel,
                itemId = selectedXiaozhantaiItemId,
                onBack = { destination = AppDestination.XiaozhantaiList },
            )
        }
    }
}

private enum class AppDestination {
    Chat,
    ParentSettings,
    ParentReport,
    XiaozhantaiList,
    XiaozhantaiPickForStrangeDoor,
    XiaozhantaiDetail,
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
