package com.childai.companion.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import com.childai.companion.ui.chat.ChildChatScreen
import com.childai.companion.ui.parent.ParentReportScreen
import com.childai.companion.ui.parent.ParentSettingsScreen

@Composable
fun AppNavHost() {
    var destination by rememberSaveable { mutableStateOf(AppDestination.Chat) }

    when (destination) {
        AppDestination.Chat -> ChildChatScreen(
            onOpenParentSettings = { destination = AppDestination.ParentSettings },
            onOpenParentReport = { destination = AppDestination.ParentReport },
        )
        AppDestination.ParentSettings -> ParentSettingsScreen(
            onBack = { destination = AppDestination.Chat },
        )
        AppDestination.ParentReport -> ParentReportScreen(
            onBack = { destination = AppDestination.Chat },
        )
    }
}

private enum class AppDestination {
    Chat,
    ParentSettings,
    ParentReport,
}
